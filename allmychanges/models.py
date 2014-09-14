# -*- coding: utf-8 -*-
from django.template.defaultfilters import linebreaksbr, urlize
import os
import re
import datetime

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager as BaseUserManager

from twiggy_goodies.threading import log

from allmychanges.crawler import search_changelog, parse_changelog
from allmychanges.crawler.git_crawler import aggregate_git_log
from allmychanges.utils import (
    cd,
    get_package_metadata,
    download_repo,
    get_commit_type,
    get_markup_type,
    get_clean_text_from_markup_text,
)
from allmychanges.tasks import update_repo


MARKUP_CHOICES = (
    ('markdown', 'markdown'),
    ('rest', 'rest'),
)
NAME_LENGTH = 80
NAMESPACE_LENGTH = 80


# based on http://www.caktusgroup.com/blog/2013/08/07/migrating-custom-user-model-django/

from pytz import common_timezones
TIMEZONE_CHOICES = [(tz, tz) for tz in common_timezones]


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
        return super(UserManager, self).create(*args, **kwargs)

    def create_user(self, username, email=None, password=None, **extra_fields):
        if email and self.filter(email=email).count() > 0:
            raise ValueError('User with email "{0}" already exists'.format(email))
        return self._create_user(username, email, password,
                                 **extra_fields)


class User(AbstractBaseUser):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    username = models.CharField('user name', max_length=254, unique=True)
    email = models.EmailField('email address', max_length=254, blank=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    timezone = models.CharField(max_length=100,
                                choices=TIMEZONE_CHOICES,
                                default='UTC')
    changelogs = models.ManyToManyField('Changelog', through='ChangelogTrack',
                                        related_name='trackers')
    moderated_changelogs = models.ManyToManyField('Changelog', through='Moderator',
                                                  related_name='moderators')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def does_track(self, changelog):
        """Check if this user tracks given changelog."""
        return self.changelogs.filter(pk=changelog.pk).count() == 1

    def track(self, changelog):
        if not self.does_track(changelog):
            ChangelogTrack.objects.create(
                user=self,
                changelog=changelog)

    def untrack(self, changelog):
        if self.does_track(changelog):
            ChangelogTrack.objects.filter(
                user=self,
                changelog=changelog).delete()


class Repo(models.Model):
    PROCESSING_STATE_CHOICES = (
        ('ready_for_job', 'Ready for job'),
        ('in_progress', 'In progress'),
        ('error', 'Error'),
        ('finished', 'Finished'),
    )

    url = models.URLField(unique=True)
    title = models.CharField(max_length=255)
    changelog_markup = models.CharField(max_length=20,
                                        choices=MARKUP_CHOICES,
                                        blank=True,
                                        null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    requested_count = models.PositiveIntegerField(default=0)

    # processing fields
    processing_state = models.CharField(max_length=20,
                                        choices=PROCESSING_STATE_CHOICES,
                                        null=True)
    processing_status_message = models.CharField(max_length=255,
                                                 blank=True,
                                                 null=True)
    processing_progress = models.PositiveIntegerField(default=0)
    processing_date_started = models.DateTimeField(blank=True, null=True)
    processing_date_finished = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'{url}. {title}'.format(url=self.url, title=self.title)

    @classmethod
    def start_changelog_processing_for_url(cls, url):
        repo, is_created = Repo.objects.get_or_create(url=url)
        repo.requested_count += 1
        if is_created:
            repo.date_created = timezone.now()
        repo.save()
        repo.start_processing_if_needed()
        return repo

    def start_processing_if_needed(self):
        if self.is_need_processing:
            self.start_changelog_processing()
            return True
        else:
            return False

    @property
    def is_need_processing(self):
        if self.processing_state == 'ready_for_job':
            return True
        elif not self.processing_date_started:
            return True
        elif self.is_processing_started_more_than_minutes_ago(30):
            return True
        elif (self.is_processing_started_more_than_minutes_ago(5)
              and self.processing_state == 'finished'):
            return True
        elif (self.is_processing_started_more_than_minutes_ago(1)
              and self.processing_state == 'error'):
            return True
        else:
            return False

    def is_processing_started_more_than_minutes_ago(self, minutes):
        return timezone.now() > (self.processing_date_started +
                        datetime.timedelta(minutes=minutes))

    def start_changelog_processing(self):
        self.processing_state = 'ready_for_job'
        self.processing_status_message = 'Ready for job'
        self.processing_progress = 10
        self.save()
        update_repo.delay(self.id)

    def _update(self):
        """Updates changelog (usually in background)."""
        self.processing_state = 'in_progress'
        self.processing_status_message = 'Downloading code'
        self.processing_progress = 50
        self.processing_date_started = timezone.now()
        self.save()

        try:
            path = download_repo(self.url)

            if path:
                with cd(path):
                    self.processing_status_message = 'Searching changes'
                    self.processing_progress = 50
                    self.save()
                    changelog_filename = search_changelog()[0]
                    if changelog_filename:
                        full_filename = os.path.normpath(
                            os.path.join(os.getcwd(), changelog_filename))

                        self._update_from_filename(full_filename)
                    else:
                        self._update_from_git_log(path)
            else:
                self.processing_state = 'error'
                self.processing_status_message = \
                    'Could not download repository'
                self.processing_date_finished = timezone.now()
                self.save()

        except Exception as e:
            self.processing_state = 'error'
            self.processing_status_message = str(e)[:255]
            self.processing_progress = 100
            self.processing_date_finished = timezone.now()
            self.save()
            raise

    def _update_from_git_log(self, path):
        progress = self.processing_progress
        progress_on_this_step = 30

        def progress_callback(git_progress):
            self.processing_progress = progress + (
                progress_on_this_step * git_progress)
            self.save()

        changes = aggregate_git_log(path, progress_callback)
        if changes:
            self._update_from_changes(changes)

    def _update_from_filename(self, filename):
        with open(filename) as f:
            self.changelog_markup = get_markup_type(filename)
            self.processing_status_message = 'Parsing changelog'
            self.processing_progress = 60
            self.save()
            changes = parse_changelog(f.read())
            self._update_from_changes(changes)

    def _update_from_changes(self, changes):
        """Update changelog in database, taking data
        from python-structured changelog."""
        self.title = get_package_metadata('.', 'Name')
        if self.title is None:
            self.title = self.url.rsplit('/', 1)[-1]

        if changes:
            self.versions.all().delete()
            self.processing_status_message = 'Updating database'
            self.processing_progress = 80
            self.save()

            for change in changes:
                version = self.versions \
                              .create(name=change['version'] or 'unrecognized',
                                      date=change.get('date'))

                for section in change['sections']:

                    item = version.items.create(
                        text=get_clean_text_from_markup_text(
                            section['notes'],
                            markup_type=self.changelog_markup))

                    for section_item in section['items']:
                        item.changes.create(
                            type=get_commit_type(section_item),
                            text=get_clean_text_from_markup_text(
                                section_item,
                                markup_type=self.changelog_markup))

                        self.processing_state = 'finished'
                        self.processing_status_message = 'Done'
                        self.processing_progress = 100
                        self.processing_date_finished = timezone.now()
        else:
            self.processing_state = 'error'
            self.processing_status_message = 'Changelog not found'
            self.processing_progress = 100
            self.processing_date_finished = timezone.now()

        self.save()


class RepoVersion(models.Model):
    repo = models.ForeignKey(Repo, related_name='versions')
    date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class RepoVersionItem(models.Model):
    version = models.ForeignKey(RepoVersion, related_name='items')
    text = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.text

    @property
    def text_clean(self):
        return '<p>%s</p>' % linebreaksbr(urlize(self.text)) \
            .replace('<br />', '</p><p>')


class RepoVersionItemChange(models.Model):
    REPO_VERSION_ITEM_CHANGE_TYPE_CHOICES = (
        ('new', 'new'),
        ('fix', 'fix'),
    )

    version_item = models.ForeignKey(RepoVersionItem, related_name='changes')
    type = models.CharField(max_length=10,
                            choices=REPO_VERSION_ITEM_CHANGE_TYPE_CHOICES)
    text = models.TextField()


class Subscription(models.Model):
    email = models.EmailField()
    come_from = models.CharField(max_length=100)
    date_created = models.DateTimeField()

    def __unicode__(self):
        return self.email


class IgnoreCheckSetters(object):
    """A mixin to get/set ignore and check lists on a model.
    """
    def _split(self, text):
        return re.split(r'[\n,]', text)

    def get_ignore_list(self):
        """Returns a list with all filenames and directories to ignore
        when searching a changelog."""
        filenames = [name.strip()
                     for name in self._split(self.ignore_list)]
        filenames = filter(None, filenames)
        return filenames

    def set_ignore_list(self, items):
        self.ignore_list = u'\n'.join(items)

    def get_check_list(self):
        """Returns a list with all filenames and directories to check
        when searching a changelog."""
        def process(name):
            name = name.strip()
            if not name:
                return None
            elif ':' in name:
                return name.split(':', 1)
            else:
                return (name, None)

        filenames = map(process, self._split(self.check_list))
        filenames = filter(None, filenames)
        return filenames

    def set_check_list(self, items):
        def process(item):
            if isinstance(item, tuple) and item[1]:
                return u':'.join(item)
            else:
                return item
        self.check_list = u'\n'.join(map(process, items))



class Changelog(IgnoreCheckSetters, models.Model):
    source = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(blank=True, null=True)
    problem = models.CharField(max_length=1000,
                               help_text='Latest error message',
                               blank=True, null=True)
    filename = models.CharField(max_length=1000,
                               help_text=('If changelog was discovered, then '
                                          'field will store it\'s filename'),
                               blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    next_update_at = models.DateTimeField(default=timezone.now)
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
    check_list = models.CharField(max_length=1000,
                                  default='',
                                  help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                  blank=True)
    namespace = models.CharField(max_length=NAMESPACE_LENGTH, blank=True, null=True)
    name = models.CharField(max_length=NAME_LENGTH, blank=True, null=True)


    class Meta:
        unique_together = ('namespace', 'name')

    def __unicode__(self):
        return u'Changelog from {0}'.format(self.source)

    def latest_version(self):
        versions = list(
            self.versions.exclude(unreleased=True) \
                         .order_by('-discovered_at', '-number')[:1])
        if versions:
            return versions[0]


    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('package', kwargs=dict(
            namespace=self.namespace,
            name=self.name))

    def editable_by(self, user, light_user=None):
        light_moderators = set(self.light_moderators.values_list('light_user', flat=True))
        moderators = set(self.moderators.values_list('id', flat=True))

        if user.is_authenticated():
            if moderators or light_moderators:
                return user.id in moderators
        else:
            if moderators or light_moderators:
                return light_user in light_moderators
        return True

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


class ChangelogTrack(models.Model):
    user = models.ForeignKey(User)
    changelog = models.ForeignKey(Changelog)
    created_at = models.DateTimeField(default=timezone.now)


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
    changelog = models.ForeignKey(Changelog)
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    from_light_user = models.CharField(max_length=40, blank=True, null=True)


class Preview(IgnoreCheckSetters, models.Model):
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
    check_list = models.CharField(max_length=1000,
                                  default='',
                                  help_text=('Comma-separated list of directories'
                                              ' and filenames to search'
                                              ' changelog.'),
                                  blank=True)
    problem = models.CharField(max_length=1000,
                               help_text='Latest error message',
                               blank=True, null=True)


class VersionManager(models.Manager):
    def get_query_set(self):
        # TODO: rename after migration to Django 1.6
        return super(VersionManager, self).get_query_set().order_by('-id')


CODE_VERSIONS = [
    ('v1', 'Old parser'),
    ('v2', 'New parser')]


class Version(models.Model):
    changelog = models.ForeignKey(Changelog, related_name='versions')
    preview = models.ForeignKey(Preview,
                                related_name='versions',
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL)

    date = models.DateField(blank=True, null=True)
    number = models.CharField(max_length=255)
    unreleased = models.BooleanField(default=False)
    discovered_at = models.DateTimeField(blank=True, null=True)
    code_version = models.CharField(max_length=255, choices=CODE_VERSIONS)
    filename = models.CharField(max_length=1000,
                                help_text=('Source file where this version was found'),
                                blank=True, null=True)
    objects = VersionManager()

    class Meta:
        get_latest_by = 'discovered_at'

    def __unicode__(self):
        return self.number


class Section(models.Model):
    version = models.ForeignKey(Version, related_name='sections')
    notes = models.TextField(blank=True, null=True)
    code_version = models.CharField(max_length=255, choices=CODE_VERSIONS)

    def __unicode__(self):
        return self.notes



class Item(models.Model):
    CHANGE_TYPES = (
        ('new', 'new'),
        ('fix', 'fix'),
    )

    section = models.ForeignKey(Section, related_name='items')
    type = models.CharField(max_length=10, choices=CHANGE_TYPES)
    text = models.TextField()


class Package(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='packages')
    namespace = models.CharField(max_length=NAMESPACE_LENGTH)
    name = models.CharField(max_length=NAME_LENGTH)
    source = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    repo = models.OneToOneField(Repo,
                                related_name='package',
                                blank=True, null=True)
    changelog = models.ForeignKey(Changelog,
                                  related_name='packages',
                                  blank=True, null=True,
                                  on_delete=models.SET_NULL)

    def __init__(self, *args, **kwargs):
        raise RuntimeError('Dont use packages anymore!')

    class Meta:
        unique_together = ('user', 'namespace', 'name')

    def __unicode__(self):
        return u'/'.join((self.user.username, self.name))

    def latest_version(self):
        return self.changelog.latest_version()

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('package', kwargs=dict(
            username=self.user.username,
            namespace=self.namespace,
            name=self.name))

    def save(self, *args, **kwargs):
        """Create corresponding changelog object"""
        super(Package, self).save(*args, **kwargs)

        if self.changelog is None or self.changelog.source != self.source:
            changelog, created = Changelog.objects.get_or_create(source=self.source)

            # TODO: add here a check of user is moderator
            if created and self.user.username in ('svetlyak40wt', 'bessarabov'):
                changelog.namespace = self.namespace
                changelog.name = self.name
                changelog.save()

            self.changelog = changelog
            self.save()

    def update(self):
        if self.repo is None:
            self.repo, created = Repo.objects.get_or_create(url=self.source)
            self.save()

        repo = self.repo
        repo._update()

        versions = list(repo.versions.all()[:5])

        print '/'.join((self.namespace, self.name))

        if versions:
            print 'Latest versions:'
            for version in versions:
                print version
                for item in version.items.all():
                    if item.text:
                        print '   ', item.text

                    for change in item.changes.all():
                        if change.text:
                            print '  *', change.text
        else:
            print 'ChangeLog wasn\'t found.'



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
        UserHistoryLog.objects.create(user=user,
                                      light_user=light_user,
                                      action=action,
                                      description=description)
