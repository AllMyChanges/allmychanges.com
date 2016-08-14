# -*- coding: utf-8 -*-
import os
import requests
import time
import math
import datetime
import random
import envoy
import jsonfield
import logging
import urllib

from collections import defaultdict
from magic_repr import make_repr
from hashlib import md5, sha1
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager as BaseUserManager
from django.core.cache import cache

#from south.modelsinspector import add_introspection_rules

from twiggy_goodies.threading import log

from allmychanges.validators import URLValidator
from allmychanges.downloaders.utils import normalize_url
from allmychanges.issues import calculate_issue_importance
from allmychanges.utils import (
    split_filenames,
    parse_search_list,
    get_one_or_none,
)
from allmychanges import chat
from allmychanges.downloaders import (
    get_downloader)

from allmychanges.utils import reverse
from allmychanges.tasks import (
    update_preview_task,
    update_changelog_task)

from allmychanges.exceptions import SynonymError

MARKUP_CHOICES = (
    ('markdown', 'markdown'),
    ('rest', 'rest'),
)
NAME_LENGTH = 80
NAMESPACE_LENGTH = 80
DESCRIPTION_LENGTH = 255
PROCESSING_STATUS_LENGTH = 40

# based on http://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/

from pytz import common_timezones
TIMEZONE_CHOICES = [(tz, tz) for tz in common_timezones]


class URLField(models.URLField):
    default_validators = [URLValidator()]

#add_introspection_rules([], ["^allmychanges\.models\.URLField"])



class UserManager(BaseUserManager):
    def _create_user(self, username, email=None, password=None,
                     **extra_fields):
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(username=username,
                          email=email,
                          last_login=now,
                          date_joined=now,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create(self, *args, **kwargs):
        email = kwargs.get('email')
        if email and self.filter(email=email).count() > 0:
            raise ValueError('User with email "{0}" already exists'.format(email))

        username = kwargs.get('username')
        url = settings.BASE_URL + reverse('admin-user-profile',
                                          username=username)
        chat.send(('New user <{url}|{username}> '
                   'with email "{email}" (from create)').format(
            url=url,
            username=username,
            email=email))
        return super(UserManager, self).create(*args, **kwargs)

    def create_user(self, username, email=None, password=None, **extra_fields):
        if email and self.filter(email=email).count() > 0:
            raise ValueError('User with email "{0}" already exists'.format(email))

        url = settings.BASE_URL + reverse('admin-user-profile',
                                          username=username)
        chat.send(('New user <{url}|{username}> '
                   'with email "{email}" (from create_user)').format(
            url=url,
            username=username,
            email=email))
        return self._create_user(username, email, password,
                                 **extra_fields)

    def active_users(self, interval):
        """Outputs only users who was active in last `interval` days.
        """
        after = timezone.now() - datetime.timedelta(interval)
        queryset = self.all()
        queryset = queryset.filter(history_log__action__in=ACTIVE_USER_ACTIONS,
                                   history_log__created_at__gte=after).distinct()
        return queryset


SEND_DIGEST_CHOICES = (
    ('daily', 'Every day'),
    ('weekly', 'Every week (on Monday)'),
    ('never', 'Never'))


RSS_HASH_LENGH = 32


class User(AbstractBaseUser):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    username = models.CharField('user name', max_length=254, unique=True)
    email = models.EmailField('email address', max_length=254)
    email_is_valid = models.BooleanField(default=False)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    timezone = models.CharField(max_length=100,
                                choices=TIMEZONE_CHOICES,
                                default='UTC')
    changelogs = models.ManyToManyField('Changelog',
                                        through='ChangelogTrack',
                                        related_name='trackers')
    feed_versions = models.ManyToManyField('Version',
                                           through='FeedItem',
                                           related_name='users')
    feed_sent_id = models.IntegerField(
        default=0,
        help_text='Keeps position in feed items already sent in digest emails')
    last_digest_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Date when last email digest was sent')
    skips_changelogs = models.ManyToManyField('Changelog',
                                              through='ChangelogSkip',
                                              related_name='skipped_by')
    moderated_changelogs = models.ManyToManyField('Changelog',
                                                  through='Moderator',
                                                  related_name='moderators')

    # notification settings
    send_digest = models.CharField(max_length=100,
                                   choices=SEND_DIGEST_CHOICES,
                                   default='daily')
    slack_url = models.URLField(max_length=2000,
                                default='',
                                blank=True)
    webhook_url = models.URLField(max_length=2000,
                                  default='',
                                  blank=True)
    rss_hash = models.CharField(max_length=RSS_HASH_LENGH,
                                unique=True,
                                blank=True,
                                null=True)
    custom_fields = jsonfield.JSONField(
        default={},
        help_text='Custom fields such like "Location" or "SecondEmail".',
        blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    __repr__ = make_repr('username', 'email')

    def get_avatar(self, size):
#        adorable_template = 'https://api.adorable.io/avatars/{size}/{hash}.png'
        robohash_template = 'https://robohash.org/{hash}.png?size={size}x{size}'

        if self.email:
            hash = md5(self.email.lower()).hexdigest()
            default = robohash_template.format(size=size, hash=hash)
            avatar_url = 'https://www.gravatar.com/avatar/{hash}?{opts}'.format(
                hash=hash,
                opts=urllib.urlencode(
                    dict(
                        s=str(size),
                        d=default
                    )
                )
            )
        else:
            hash = md5(self.username).hexdigest()
            avatar_url = robohash_template.format(size=size, hash=hash)

        return avatar_url


    @property
    def is_superuser(self):
        return self.username in settings.SUPERUSERS

    def does_track(self, changelog):
        """Check if this user tracks given changelog."""
        return self.changelogs.filter(pk=changelog.id).exists()

    def track(self, changelog):
        if not self.does_track(changelog):
            if changelog.namespace == 'web' and changelog.name == 'allmychanges':
                action = 'track-allmychanges'
                action_description = 'User tracked our project\'s changelog.'
            else:
                action = 'track'
                action_description = 'User tracked changelog:{0}'.format(changelog.id)

            UserHistoryLog.write(self, '', action, action_description)

            ChangelogTrack.objects.create(
                user=self,
                changelog=changelog)

    def untrack(self, changelog):
        if self.does_track(changelog):
            if changelog.namespace == 'web' and changelog.name == 'allmychanges':
                action = 'untrack-allmychanges'
                action_description = 'User untracked our project\'s changelog.'
            else:
                action = 'untrack'
                action_description = 'User untracked changelog:{0}'.format(changelog.id)

            UserHistoryLog.write(self, '', action, action_description)
            ChangelogTrack.objects.filter(
                user=self,
                changelog=changelog).delete()

    def does_skip(self, changelog):
        """Check if this user skipped this changelog in package selector."""
        return self.skips_changelogs.filter(pk=changelog.id).exists()

    def skip(self, changelog):
        if not self.does_skip(changelog):
            action = 'skip'
            action_description = 'User skipped changelog:{0}'.format(changelog.id)

            UserHistoryLog.write(self, '', action, action_description)
            ChangelogSkip.objects.create(
                user=self,
                changelog=changelog)

    def add_feed_item(self, version):
        if self.send_digest == 'never':
            return None

        return FeedItem.objects.create(user=self, version=version)

    def save(self, *args, **kwargs):
        if self.rss_hash is None:
            self.rss_hash = sha1(self.username + settings.SECRET_KEY).hexdigest()[:RSS_HASH_LENGH]
        return super(User, self).save(*args, **kwargs)


class Subscription(models.Model):
    email = models.EmailField()
    come_from = models.CharField(max_length=100)
    date_created = models.DateTimeField()

    def __unicode__(self):
        return self.email


class Downloadable(object):
    """Adds method download, which uses attribute `source`
    to update attribute `downloader` if needed and then to
    download repository into a temporary directory.
    """
    def download(self, downloader,
                 report_back=lambda message, level=logging.INFO: None):
        """This method fetches repository into a temporary directory
        and returns path to this directory.

        It can report about downloading status using callback `report_back`.
        Everything what will passed to `report_back`, will be displayed to
        the end user in a processing log on a "Tune" page.
        """

        if isinstance(downloader, dict):
            params = downloader.get('params', {})
            downloader = downloader['name']
        else:
            params = {}

        params.update(self.downloader_settings or {})

        download = get_downloader(downloader)
        return download(self.source,
                        report_back=report_back,
                        **params)

    # A mixin to get/set ignore and check lists on a model.
    def get_ignore_list(self):
        """Returns a list with all filenames and directories to ignore
        when searching a changelog."""
        return split_filenames(self.ignore_list)

    def set_ignore_list(self, items):
        self.ignore_list = u'\n'.join(items)

    def get_search_list(self):
        """Returns a list with all filenames and directories to check
        when searching a changelog."""
        return parse_search_list(self.search_list)

    def set_search_list(self, items):
        def process(item):
            if isinstance(item, tuple) and item[1]:
                return u':'.join(item)
            else:
                return item
        self.search_list = u'\n'.join(map(process, items))


class ChangelogManager(models.Manager):
    def only_active(self):
        # active changelog is good and not paused
        queryset = self.good()
        return queryset.filter(paused_at=None)

    def good(self):
        # good changelog should have namespace, name, source and downloader
        return self.all().exclude(
            Q(name=None) |
            Q(namespace=None) |
            Q(downloader=None) |
            Q(source=''))

    def unsuccessful(self):
        return self.all().filter(
            Q(name=None) |
            Q(namespace=None) |
            Q(downloader=None) |
            Q(source=''))


class Changelog(Downloadable, models.Model):
    objects = ChangelogManager()
    source = URLField(db_index=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: remove
    processing_started_at = models.DateTimeField(blank=True, null=True)
    problem = models.CharField(max_length=1000,
                               help_text='Latest error message',
                               blank=True, null=True)
    # TODO: remove
    filename = models.CharField(max_length=1000,
                               help_text=('If changelog was discovered, then '
                                          'field will store it\'s filename'),
                               blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    next_update_at = models.DateTimeField(default=timezone.now)
    paused_at = models.DateTimeField(blank=True, null=True)
    last_update_took = models.IntegerField(
        help_text=('Number of seconds required to '
                   'update this changelog last time'),
        default=0)
    ignore_list = models.CharField(max_length=1000,
                                   default='',
                                   help_text=('Comma-separated list of directories'
                                              ' and filenames to ignore searching'
                                              ' changelog.'),
                                   blank=True)
    # TODO: выяснить зачем тут два поля check_list и search_list
    check_list = models.CharField(max_length=1000,
                                   default='',
                                   help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                   blank=True)
    search_list = models.CharField(max_length=1000,
                                  default='',
                                  help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                  blank=True)
    xslt = models.TextField(default='',
                            help_text=('XSLT transform to be applied to all html files.'),
                            blank=True)
    namespace = models.CharField(max_length=NAMESPACE_LENGTH, blank=True, null=True)
    name = models.CharField(max_length=NAME_LENGTH, blank=True, null=True)
    description = models.CharField(max_length=DESCRIPTION_LENGTH,
                                   blank=True,
                                   default='')
    downloader = models.CharField(max_length=20, blank=True, null=True)
    downloader_settings = jsonfield.JSONField(
        default={},
        help_text=('JSON with settings for selected downloader.'),
        blank=True)
    downloaders = jsonfield.JSONField(
        default=[],
        help_text=('JSON with guessed downloaders and their additional meta information.'),
        blank=True)

    status = models.CharField(max_length=40, default='created')
    processing_status = models.CharField(max_length=PROCESSING_STATUS_LENGTH)
    icon = models.CharField(max_length=1000,
                            blank=True, null=True)

    class Meta:
        unique_together = ('namespace', 'name')

    def __unicode__(self):
        return u'Changelog from {0}'.format(self.source)

    __repr__ = make_repr('namespace', 'name', 'source')

    def latest_versions(self, limit):
        return self.versions.exclude(unreleased=True) \
                            .order_by('-order_idx')[:limit]
    def latest_version(self):
        versions = list(self.latest_versions(1))
        if versions:
            return versions[0]

    def get_display_name(self):
        return u'{0}/{1}'.format(
            self.namespace,
            self.name)

    @staticmethod
    def create_uniq_name(namespace, name):
        """Returns a name which is unique in given namespace.
        Name is created by incrementing a value."""
        if namespace and name:
            base_name = name
            counter = 0

            while Changelog.objects.filter(
                    namespace=namespace,
                    name=name).exists():
                counter += 1
                name = '{0}{1}'.format(base_name, counter)
        return name

    @staticmethod
    def get_all_namespaces(like=None):
        queryset = Changelog.objects.all()
        if like is not None:
            queryset = queryset.filter(
                namespace__iexact=like
            )
        return list(queryset.values_list('namespace', flat=True).distinct())

    @staticmethod
    def normalize_namespaces():
        namespaces_usage = defaultdict(int)
        changelogs_with_namespaces = Changelog.objects.exclude(namespace=None)

        for namespace in changelogs_with_namespaces.values_list('namespace', flat=True):
            namespaces_usage[namespace] += 1

        def normalize(namespace):
            lowercased = namespace.lower()
            # here we process only capitalized namespaces
            if namespace == lowercased:
                return

            # if there lowercased is not used at all
            if lowercased not in namespaces_usage:
                return

            lowercased_count = namespaces_usage[lowercased]
            this_count = namespaces_usage[namespace]

            if lowercased_count >= this_count:
                # if num of occurences is equal,
                # prefer lowercased name
                Changelog.objects.filter(
                    namespace=namespace).update(
                        namespace=lowercased)
            else:
                Changelog.objects.filter(
                    namespace=lowercased).update(
                        namespace=namespace)

            del namespaces_usage[namespace]
            del namespaces_usage[lowercased]

        all_namespaces = namespaces_usage.keys()
        all_namespaces.sort()

        for namespace in all_namespaces:
            normalize(namespace)


    def save(self, *args, **kwargs):
        if self.id is None:
            # than objects just created and this is good
            # time to fix it's namespace
            existing_namespaces = Changelog.get_all_namespaces(like=self.namespace)
            if existing_namespaces:
                self.namespace = existing_namespaces[0]

        return super(Changelog, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('project',
                       namespace=self.namespace,
                       name=self.name)

    def editable_by(self, user, light_user=None):
        light_moderators = set(self.light_moderators.values_list('light_user', flat=True))
        moderators = set(self.moderators.values_list('id', flat=True))

        if user.is_authenticated():
            # Any changelog could be edited by me
            if user.is_superuser:
                return True

            if moderators or light_moderators:
                return user.id in moderators
        else:
            if moderators or light_moderators:
                return light_user in light_moderators
        return True

    def is_unsuccessful(self):
        return self.name is None or \
               self.namespace is None or \
               self.downloader is None or \
               not self.source

    def is_moderator(self, user, light_user=None):
        light_moderators = set(self.light_moderators.values_list('light_user', flat=True))
        moderators = set(self.moderators.values_list('id', flat=True))

        if user.is_authenticated():
            return user.id in moderators
        else:
            return light_user in light_moderators

    def add_to_moderators(self, user, light_user=None):
        """Adds user to moderators and returns 'normal' or 'light'
        if it really added him.
        In case if user already was a moderator, returns None."""

        if not self.is_moderator(user, light_user):
            if user.is_authenticated():
                Moderator.objects.create(changelog=self, user=user)
                return 'normal'
            else:
                if light_user is not None:
                    self.light_moderators.create(light_user=light_user)
                    return 'light'

    def create_issue(self, type, comment='', related_versions=[]):
        joined_versions = u', '.join(related_versions)

        # for some types, only one issue at a time is allowed
        if type == 'lesser-version-count':
            if self.issues.filter(type=type, resolved_at=None, related_versions=joined_versions).count() > 0:
                return

        issue = self.issues.create(type=type,
                                   comment=comment.format(related_versions=joined_versions),
                                   related_versions=joined_versions)
        chat.send(u'New issue of type "{issue.type}" with comment: "{issue.comment}" was created for <https://allmychanges.com/issues/?namespace={issue.changelog.namespace}&name={issue.changelog.name}|{issue.changelog.namespace}/{issue.changelog.name}>'.format(
            issue=issue))

    def resolve_issues(self, type):
        self.issues.filter(type=type, resolved_at=None).update(resolved_at=timezone.now())

    def create_preview(self, user, light_user, **params):
        params.setdefault('downloader', self.downloader)
        params.setdefault('downloader_settings', self.downloader_settings)
        params.setdefault('downloaders', self.downloaders)
        params.setdefault('source', self.source)
        params.setdefault('search_list', self.search_list)
        params.setdefault('ignore_list', self.ignore_list)
        params.setdefault('xslt', self.xslt)

        preview = self.previews.create(user=user, light_user=light_user, **params)
        # preview_test_task.delay(
        #     preview.id,
        #     ['Guessing downloders',
        #      'Downloading using git',
        #      'Searching versions',
        #      'Nothing found',
        #      'Downloading from GitHub Review',
        #      'Searching versions',
        #      'Some results were found'])

        return preview

    def set_status(self, status, **kwargs):
        changed_fields = ['status', 'updated_at']
        if status == 'error':
            self.problem = kwargs.get('problem')
            changed_fields.append('problem')

        self.status = status
        self.updated_at = timezone.now()
        self.save(update_fields=changed_fields)

    def set_processing_status(self, status, level=logging.INFO):
        self.processing_status = status[:PROCESSING_STATUS_LENGTH]
        self.updated_at = timezone.now()
        self.save(update_fields=('processing_status',
                                 'updated_at'))
        key = 'preview-processing-status:{0}'.format(self.id)
        cache.set(key, status, 10 * 60)

    def get_processing_status(self):
        key = 'preview-processing-status:{0}'.format(self.id)
        result = cache.get(key, self.processing_status)
        return result

    def calc_next_update(self):
        """Returns date and time when next update should be scheduled.
        """
        hour = 60 * 60
        min_update_interval = hour
        max_update_interval = 48 * hour
        num_trackers = self.trackers.count()
        # here we divide max interval on 2 because
        # on the last stage will add some randomness to
        # the resulting value
        time_to_next_update = (max_update_interval / 2) / math.log(max(math.e,
                                                                 num_trackers))

        time_to_next_update = max(min_update_interval,
                                  time_to_next_update,
                                  2 * self.last_update_took)

        # add some randomness
        time_to_next_update = random.randint(
            int(time_to_next_update * 0.8),
            int(time_to_next_update * 2.0))

        # limit upper bound
        return timezone.now() + datetime.timedelta(0, time_to_next_update)

    def calc_next_update_if_error(self):
        # TODO: check and remove
        return timezone.now() + datetime.timedelta(0, 1 * 60 * 60)

    def schedule_update(self, async=True, full=False):
        with log.fields(changelog_name=self.name,
                        changelog_namespace=self.namespace,
                        async=async,
                        full=full):
            log.info('Scheduling changelog update')

            self.set_status('processing')
            self.set_processing_status('Waiting in the queue')

            self.problem = None
            self.save()

            if full:
                self.versions.all().delete()

            if async:
                update_changelog_task.delay(self.id)
            else:
                update_changelog_task(self.id)

    def resume(self):
        self.paused_at = None
        self.next_update_at = timezone.now()
        # we don't need to save here, because this will be done in schedule_update
        self.schedule_update()


    def clean(self):
        super(Changelog, self).clean()
        self.source, _, _ = normalize_url(self.source, for_checkout=False)

    def update_description_from_source(self, fall_asleep_on_rate_limit=False):
        # right now this works only for github urls
        if 'github.com' not in self.source:
            return

        url, username, repo = normalize_url(self.source)
        url = 'https://api.github.com/repos/{0}/{1}'.format(username, repo)

        headers={'Authorization': 'token ' + settings.GITHUB_TOKEN}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            self.description = data.get('description', '')
            self.save(update_fields=('description', ))

        if fall_asleep_on_rate_limit:
            remaining = int(response.headers['x-ratelimit-remaining'])
            if remaining == 1:
                to_sleep = int(response.headers['x-ratelimit-reset']) - time.time() + 10
                print 'OK, now I need to sleep {0} seconds because of GitHub\'s rate limit.'.format(to_sleep)
                time.sleep(to_sleep)

    def add_synonym(self, synonym):
        """Just a shortcut."""
        if self.synonyms.filter(source=synonym).count() == 0:
            # if this synonym already bound to some another project
            # then raise exception
            found = list(SourceSynonym.objects.filter(source=synonym))
            if found:
                with log.fields(changelog_id=self.pk,
                                another_changelog_id=found[0].changelog_id):
                    raise SynonymError('Synonym already bound to a changelog')

            found = list(Changelog.objects.filter(source=synonym))
            if found:
                with log.fields(changelog_id=self.pk,
                                another_changelog_id=found[0].pk):
                    raise SynonymError('Synonym matches a changelog\'s source')

            self.synonyms.create(source=synonym)

    def merge_into(self, to_ch):
        # move trackers
        to_ch_trackers = set(to_ch.trackers.values_list('id', flat=True))

        for user in self.trackers.all():
            if user.id not in to_ch_trackers:
                ChangelogTrack.objects.create(user=user, changelog=to_ch)
                action = 'moved-during-merge'
                action_description = 'User was moved from {0}/{1} to changelog:{2}'.format(
                    self.namespace,
                    self.name,
                    to_ch.id)
                UserHistoryLog.write(user, '', action, action_description)

        # move issues
        for issue in self.issues.all():
            issue.changelog = to_ch
            issue.save(update_fields=('changelog',))

        # remove itself
        Changelog.objects.filter(pk=self.pk).delete()

        # add synonym
        to_ch.add_synonym(self.source)

    def set_tag(self, user, name, version_number):
        """Sets or updates tag with `name` on the version.
        If tag was updated, returns 'updated'
        otherwise, returns 'created'
        """
        assert isinstance(version_number, basestring), \
            'Parameter "version_number" should be a string, not "{0}"'.format(
                type(version_number))

        params = dict(user=user, name=name)

        existing_tag = self.tags.filter(
            **params)

        update = existing_tag.count() > 0
        if update:
            existing_tag.delete()

        version = get_one_or_none(self.versions, number=version_number)
        self.tags.create(version=version,
                         version_number=version_number,
                         **params)

        return 'updated' if update else 'created'


    def remove_tag(self, user, name):
        """Removes tag with `name` on the version.
        """
        self.tags.filter(user=user, name=name).delete()


class SourceSynonym(models.Model):
    changelog = models.ForeignKey(Changelog, related_name='synonyms')
    created_at = models.DateTimeField(default=timezone.now)
    source = URLField(unique=True)


class ChangelogTrack(models.Model):
    user = models.ForeignKey(User)
    changelog = models.ForeignKey(Changelog)
    created_at = models.DateTimeField(default=timezone.now)


class ChangelogSkip(models.Model):
    user = models.ForeignKey(User)
    changelog = models.ForeignKey(Changelog)
    created_at = models.DateTimeField(default=timezone.now)


class Issue(models.Model):
    """Keeps track any issues, related to a changelog.
    """
    changelog = models.ForeignKey(Changelog,
                                  related_name='issues',
                                  blank=True,
                                  null=True)
    user = models.ForeignKey(User,
                             related_name='issues',
                             blank=True,
                             null=True)
    light_user = models.CharField(max_length=40, blank=True, null=True)
    type = models.CharField(max_length=40)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(User,
                                    related_name='resolved_issues',
                                    blank=True,
                                    null=True)
    related_versions = models.TextField(default='', blank=True,
                                        help_text='Comma-separated list of versions, related to this issue')
    email = models.CharField(max_length=100, blank=True, null=True)
    page = models.CharField(max_length=100, blank=True, null=True)
    importance = models.IntegerField(db_index=True, blank=True, default=0)

    __repr__ = make_repr('changelog', 'type', 'comment', 'created_at', 'resolved_at')

    def save(self, *args, **kwargs):
        if not self.importance:
            self.importance = calculate_issue_importance(
                num_trackers=self.changelog.trackers.count()
                             if self.changelog
                             else 0,
                user=self.user,
                light_user=self.light_user)
        return super(Issue, self).save(*args, **kwargs)

    @staticmethod
    def merge(user, light_user):
        entries = Issue.objects.filter(user=None,
                                                light_user=light_user)
        if entries.count() > 0:
            with log.fields(username=user.username,
                            num_entries=entries.count(),
                            light_user=light_user):
                log.info('Merging issues')
                entries.update(user=user)

    def editable_by(self, user, light_user=None):
        return self.changelog.editable_by(user, light_user)

    def get_related_versions(self):
        response = [version.strip()
                    for version in self.related_versions.split(',')]
        return filter(None, response)

    def get_related_deployments(self):
        return DeploymentHistory.objects \
            .filter(deployed_at__lte=self.created_at) \
            .order_by('-id')[:3]

    def resolve(self, user, notify=True):
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save(update_fields=('resolved_at', 'resolved_by'))

        if notify:
            chat.send((u'Issue <https://allmychanges.com{url}|#{issue_id}> '
                       u'for {namespace}/{name} was resolved by {username}.').format(
                url=reverse('issue-detail', pk=self.id),
                issue_id=self.id,
                namespace=self.changelog.namespace,
                name=self.changelog.name,
                username=user.username))

        if self.type == 'auto-paused':
            changelog = self.changelog
            with log.fields(changelog_id=changelog.id):
                log.info('Resuming changelog updates')
                changelog.resume()

                if notify:
                    chat.send(u'Autopaused package {namespace}/{name} was resumed {username}.'.format(
                        namespace=changelog.namespace,
                        name=changelog.name,
                        username=user.username))



class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, related_name='comments')
    user = models.ForeignKey(User, blank=True, null=True,
                             related_name='issue_comments')
    created_at = models.DateTimeField(default=timezone.now)
    message = models.TextField()


class DiscoveryHistory(models.Model):
    """Keeps track any issues, related to a changelog.
    """
    changelog = models.ForeignKey(Changelog,
                                  related_name='discovery_history')
    discovered_versions = models.TextField()
    new_versions = models.TextField()
    num_discovered_versions = models.IntegerField()
    num_new_versions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


    __repr__ = make_repr('discovered_versions')


class LightModerator(models.Model):
    """These entries are created when anonymouse user
    adds another package into the system.
    When user signs up, these entries should be
    transformed into the Moderator entries.
    """
    changelog = models.ForeignKey(Changelog,
                                  related_name='light_moderators')
    light_user = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def merge(user, light_user):
        entries = LightModerator.objects.filter(light_user=light_user)
        for entry in entries:
            with log.fields(username=user.username,
                            light_user=light_user):
                log.info('Transforming light moderator into the permanent')
                Moderator.objects.create(
                    changelog=entry.changelog,
                    user=user,
                    from_light_user=light_user)
        entries.delete()

    @staticmethod
    def remove_stale_moderators():
        LightModerator.objects.filter(
            created_at__lte=timezone.now() - datetime.timedelta(1)).delete()


class Moderator(models.Model):
    changelog = models.ForeignKey(Changelog, related_name='+')
    user = models.ForeignKey(User, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    from_light_user = models.CharField(max_length=40, blank=True, null=True)


class Preview(Downloadable, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='previews',
                             blank=True,
                             null=True)
    changelog = models.ForeignKey(Changelog,
                                  related_name='previews')
    light_user = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    source = models.URLField()
    ignore_list = models.CharField(max_length=1000,
                                   default='',
                                   help_text=('Comma-separated list of directories'
                                              ' and filenames to ignore searching'
                                              ' changelog.'),
                                   blank=True)
    # TODO: remove this field after migration on production
    check_list = models.CharField(max_length=1000,
                                  default='',
                                  help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                  blank=True)
    search_list = models.CharField(max_length=1000,
                                   default='',
                                   help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                   blank=True)
    xslt = models.TextField(default='',
                            help_text=('XSLT transform to be applied to all html files.'),
                            blank=True)
    problem = models.CharField(max_length=1000,
                               help_text='Latest error message',
                               blank=True, null=True)
    downloader = models.CharField(max_length=255, blank=True, null=True)
    downloader_settings = jsonfield.JSONField(
        default={},
        help_text=('JSON with settings for selected downloader.'),
        blank=True)
    downloaders = jsonfield.JSONField(
        default=[],
        help_text=('JSON with guessed downloaders and their additional meta information.'),
        blank=True)
    done = models.BooleanField(default=False)
    status = models.CharField(max_length=40, default='created')
    processing_status = models.CharField(max_length=40)
    log = jsonfield.JSONField(default=[],
                              help_text=('JSON with log of all operation applied during preview processing.'),
                              blank=True)

    @property
    def namespace(self):
        return self.changelog.namespace

    @property
    def name(self):
        return self.changelog.name

    @property
    def description(self):
        return self.changelog.description

    def set_status(self, status, **kwargs):
        changed_fields = ['status', 'updated_at']
        if status == 'processing':
            self.versions.all().delete()
            self.updated_at = timezone.now()
            changed_fields.append('updated_at')

        elif status == 'error':
            self.problem = kwargs.get('problem')
            changed_fields.append('problem')

        self.status = status
        self.updated_at = timezone.now()
        self.save(update_fields=changed_fields)


    def set_processing_status(self, status, level=logging.INFO):
        self.log.append(status)
        self.processing_status = status[:PROCESSING_STATUS_LENGTH]
        self.updated_at = timezone.now()

        self.save(update_fields=('processing_status',
                                 'updated_at',
                                 'log'))
        key = 'preview-processing-status:{0}'.format(self.id)
        cache.set(key, status, 10 * 60)

    def get_processing_status(self):
        key = 'preview-processing-status:{0}'.format(self.id)
        result = cache.get(key, self.processing_status)
        return result

    def schedule_update(self):
        self.set_status('processing')
        self.set_processing_status('Waiting in the queue')
        self.versions.all().delete()
        update_preview_task.delay(self.pk)


class VersionManager(models.Manager):
    use_for_related_fields = True

    def create(self, *args, **kwargs):
        version = super(VersionManager, self).create(*args, **kwargs)
        changelog = kwargs.get('changelog')

        if changelog:
            version.associate_with_free_tags()
        return version

    def released(self):
        return self.exclude(unreleased=True)

    def unreleased(self):
        return self.filter(unreleased=True)



class Version(models.Model):
    changelog = models.ForeignKey(Changelog,
                                  related_name='versions',
                                  blank=True,
                                  null=True,
                                  on_delete=models.SET_NULL)
    preview = models.ForeignKey(Preview,
                                related_name='versions',
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL)

    date = models.DateField(blank=True, null=True)
    number = models.CharField(max_length=255)
    unreleased = models.BooleanField(default=False)
    discovered_at = models.DateTimeField(blank=True, null=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    filename = models.CharField(max_length=1000,
                                help_text=('Source file where this version was found'),
                                blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)
    processed_text = models.TextField(blank=True, null=True)
    order_idx = models.IntegerField(blank=True, null=True,
                                    help_text=('This field is used to reorder versions '
                                               'according their version numbers and to '
                                               'fetch them from database efficiently.'))
    tweet_id = models.CharField(max_length=1000,
                                help_text=('Tweet id or None if we did not tweeted about this version yet.'),
                                blank=True,
                                null=True)
    objects = VersionManager()

    class Meta:
        get_latest_by = 'order_idx'
        ordering = ['-order_idx']

    def __unicode__(self):
        return self.number

    def get_absolute_url(self):
        return self.changelog.get_absolute_url() + '#' + self.number

    def post_tweet(self):
        if not settings.TWITTER_CREDS:
            return

        if self.unreleased:
            raise RuntimeError('Unable to tweet about unreleased version')

        if self.tweet_id:
            return # because we already posted a tweet


        ch = self.changelog
        image_url = settings.BASE_URL + ch.get_absolute_url() \
                    + '?snap=1&version=' + self.number
        filename = sha1(image_url).hexdigest() + '.png'
        full_path = os.path.join(settings.SNAPSHOTS_ROOT, filename)


        result = envoy.run(
            '{root}/makescreenshot --width 590 --height 600 {url} {path}'.format(
                root=settings.PROJECT_ROOT,
                url=image_url,
                path=full_path))

        if result.status_code != 0:
            with log.fields(
                    status_code=result.status_code,
                    std_out=result.std_out,
                    std_err=result.std_err):
                log.error('Unable to make a screenshot')
                raise RuntimeError('Unable to make a screenshot')

        with open(full_path, 'rb') as f:
            from requests_oauthlib import OAuth1
            auth = OAuth1(*settings.TWITTER_CREDS)
            response = requests.post(
                'https://upload.twitter.com/1.1/media/upload.json',
                auth=auth,
                files={'media': ('screenshot.png',
                                 f.read(), 'image/png')})
            media_id = response.json()['media_id_string']

            url = settings.BASE_URL + self.get_absolute_url()
            text = '{number} of {namespace}/{name} was released: {url} #{namespace} #{name} #release'.format(
                number=self.number,
                namespace=ch.namespace,
                name=ch.name,
                url=url)
            response = requests.post(
                'https://api.twitter.com/1.1/statuses/update.json',
                auth=auth,
                data={'status': text,
                      'media_ids': media_id})
            if response.status_code == 200:
                self.tweet_id = response.json()['id_str']
                self.save(update_fields=('tweet_id',))
        return full_path

    def set_tag(self, user, name):
        """Convenience method to set tag on just this version.
        """
        self.changelog.set_tag(user, name, self.number)

    def associate_with_free_tags(self):
        # associate free tags with this version
        for tag in self.changelog.tags.filter(version_number=self.number):
            tag.version = self
            tag.save(update_fields=('version',))


class Tag(models.Model):
    # this field shouldn't be blank or null
    # but I have to make it so, because otherwise
    # DB migrations wasn't possible
    changelog = models.ForeignKey(Changelog,
                                  blank=True,
                                  null=True,
                                  related_name='tags')
    # tag may be tied to a version in the database,
    # but in some cases, we may don't have parsed version
    # with given number
    version = models.ForeignKey(Version,
                                blank=True,
                                null=True,
                                related_name='tags')
    user = models.ForeignKey(User, related_name='tags')
    # regex=ur'[a-z][a-z0-9-]*[a-z0-9]'
    name = models.CharField(max_length=40)
    # we have not any restrictions on the format of this field
    # this could be any string even something like 'latest'
    version_number = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('changelog', 'user', 'name')

    def get_absolute_url(self):
        # the name shouldn't contain any unicode or nonascii letters nor spaces
        # otherwise, we need to encode tu utf-8 and quote_plus it.
        return self.changelog.get_absolute_url() + '#' + self.name

    __repr__ = make_repr('name', 'version_number')


class FeedItem(models.Model):
    user = models.ForeignKey(User)
    version = models.ForeignKey(Version, related_name='feed_items')
    created_at = models.DateTimeField(auto_now_add=True)


ACTIVE_USER_ACTIONS = (
    u'landing-digest-view', u'landing-track', u'landing-ignore',
    u'login', u'profile-update', u'digest-view',
    u'package-view', u'package-create', u'package-edit',
    u'edit-digest-view', u'index-view', u'track', u'untrack',
    u'untrack-allmychanges', u'create-issue',
    u'email-digest-open', u'email-digest-click')


class UserHistoryLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='history_log',
                             blank=True,
                             null=True)
    light_user = models.CharField(max_length=40)
    action = models.CharField(max_length=40)
    description = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)


    @staticmethod
    def merge(user, light_user):
        entries = UserHistoryLog.objects.filter(user=None,
                                                light_user=light_user)
        if entries.count() > 0:
            with log.fields(username=user.username,
                            num_entries=entries.count(),
                            light_user=light_user):
                log.info('Merging user history logs')
                entries.update(user=user)

    @staticmethod
    def write(user, light_user, action, description):
        user = user if user is not None and user.is_authenticated() else None
        return UserHistoryLog.objects.create(user=user,
                                             light_user=light_user,
                                             action=action,
                                             description=description)


class UserStateHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='state_history')
    date = models.DateField()
    state = models.CharField(max_length=40)


class DeploymentHistory(models.Model):
    hash = models.CharField(max_length=32, default='')
    description = models.TextField()
    deployed_at = models.DateTimeField(auto_now_add=True)

    __repr__ = make_repr('deployed_at', 'hash')


class EmailVerificationCode(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='email_verification_code')
    hash = models.CharField(max_length=32, default='')
    deployed_at = models.DateTimeField(auto_now_add=True)


    @staticmethod
    def new_code_for(user):
        hash = md5(str(time.time()) + settings.SECRET_KEY).hexdigest()

        try:
            code = user.email_verification_code
            code.hash = hash
            code.save()
        except EmailVerificationCode.DoesNotExist:
            code = EmailVerificationCode.objects.create(
                user=user,
                hash=hash)

        return code


AUTOCOMPLETE_TYPES = (
    ('source', 'Source URL'),
    ('namespace', 'Namespace'),
    ('package', 'Package'))

AUTOCOMPLETE_ORIGINS = (
    ('app-store', 'App Store'),
    ('pypi', 'PyPi'))


COMMON_WORDS = set('a,able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,ever,every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,i,if,in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,my,neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,say,says,she,should,since,so,some,than,that,the,their,them,then,there,these,they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,which,while,who,whom,why,will,with,would,yet,you,your'.split(','))


class AutocompleteData(models.Model):
    origin = models.CharField(max_length=100,
                              choices=AUTOCOMPLETE_ORIGINS)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=DESCRIPTION_LENGTH,
                                   default='')
    type = models.CharField(max_length=10,
                            choices=AUTOCOMPLETE_TYPES)
    source = models.CharField(max_length=255, # we need this because MySQL will output warning and break our migrations for greater length
                              blank=True, null=True,
                              db_index=True)
    icon = models.CharField(max_length=255,
                            blank=True, null=True)
    changelog = models.ForeignKey(Changelog,
                                  blank=True, null=True,
                                  related_name='autocomplete')
    score = models.IntegerField(default=0,
                                help_text=('A value from 0 to infinity. '
                                           'Items with bigger values '
                                           'should appear at the top '
                                           'of the suggest.'))

    __repr__ = make_repr('title')

    def save(self, *args, **kwargs):
        super(AutocompleteData, self).save(*args, **kwargs)
        if self.words.count() == 0:
            self.add_words()

    def add_words(self, db_name='default'):
        if db_name == 'default':
            data = self
        else:
            data = AutocompleteData.objects.using(db_name).get(pk=self.pk)

        words = data.title.split()
        words = (word.strip() for word in words)
        words = set(word.lower() for word in words if len(word) > 3)
        words -= COMMON_WORDS
        words.add(data.title.lower())

        words = [AutocompleteWord2.objects.using(db_name).get_or_create(word=word)[0]
                 for word in words]
        data.words2.add(*words)


class AutocompleteWord(models.Model):
    word = models.CharField(max_length=100, db_index=True)
    data = models.ForeignKey(AutocompleteData,
                             related_name='words')

    __repr__ = make_repr('word')


class AutocompleteWord2(models.Model):
    word = models.CharField(max_length=100, unique=True)
    data_objects = models.ManyToManyField(
        AutocompleteData,
        related_name='words2')

    __repr__ = make_repr('word')


class AppStoreBatch(models.Model):
    """To identify separate processing batches.
    """
    created = models.DateTimeField(auto_now_add=True)
    __repr__ = make_repr()


class AppStoreUrl(models.Model):
    """This model is used when we are fetching
    data from app store for our autocomplete.

    Use management command update_appstore_urls to populate this collection.
    """
    # we need this because MySQL will output warning and break our migrations for greater length
    source = models.CharField(max_length=255,
                              blank=True, null=True,
                              unique=True)
    autocomplete_data = models.OneToOneField(AutocompleteData,
                                             blank=True, null=True,
                                             related_name='appstore_url',
                                             on_delete=models.SET_NULL)
    batch = models.ForeignKey(AppStoreBatch,
                              blank=True, null=True,
                              related_name='urls',
                              on_delete=models.SET_NULL)
    rating = models.FloatField(blank=True, null=True)
    rating_count = models.IntegerField(blank=True, null=True)

    __repr__ = make_repr('source')


class MandrillMessage(models.Model):
    mid = models.CharField(max_length=32,
                           help_text='Mandrills ID',
                           db_index=True)
    timestamp = models.IntegerField()
    email = models.EmailField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='mandrill_messages',
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True)
    payload = models.TextField()

    __repr__ = make_repr('mid', 'email')
