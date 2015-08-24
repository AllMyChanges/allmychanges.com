# -*- coding: utf-8 -*-
import subprocess
import threading
import datetime
import anyjson
import time
import random
import requests
import os
import urllib
import re
import markdown2

from itertools import groupby
from operator import itemgetter
from hashlib import sha1
from braces.views import (LoginRequiredMixin,
                          UserPassesTestMixin)
from django.views.generic import (TemplateView,
                                  RedirectView,
                                  FormView,
                                  UpdateView,
                                  DetailView,
                                  View)
from django.contrib import messages
from django.db.models import Count
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from twiggy_goodies.threading import log

from allmychanges.models import (Version,
                                 EmailVerificationCode,
                                 Issue,
                                 LightModerator,
                                 Subscription,
                                 Changelog,
                                 User,
                                 UserHistoryLog,
                                 Preview)
from allmychanges.churn import get_user_actions_heatmap
from allmychanges import chat
from allmychanges.notifications.email import send_email
from allmychanges.http import LastModifiedMixin

from oauth2_provider.models import Application, AccessToken

from allmychanges.utils import (HOUR,
                                parse_ints,
                                join_ints)
from allmychanges.downloaders.utils import normalize_url
from allmychanges.downloaders import guess_downloaders



class SuperuserRequiredMixin(UserPassesTestMixin):
    raise_exception = True
    def get_test_func(self):
        return lambda user: user.username == 'svetlyak40wt'


class CommonContextMixin(object):
    def get_context_data(self, **kwargs):
        result = super(CommonContextMixin, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request

        key = 'track_stats_for_footer'
        stats = cache.get(key)
        if stats is None:
            num_tracked_changelogs = Changelog.objects.count()
            num_trackers = User.objects.count()
            cache.set(key,
                      (num_trackers, num_tracked_changelogs),
                      HOUR)
        else:
            num_trackers, num_tracked_changelogs = stats
        result['total_num_trackers'] = num_trackers
        result['total_num_tracked_changelogs'] = num_tracked_changelogs

        return result


class OldIndexView(TemplateView):
    template_name = 'allmychanges/index.html'

    def get_context_data(self, **kwargs):
        result = super(OldIndexView, self).get_context_data(**kwargs)
        result['settings'] = settings
        return result


class SubscriptionForm(forms.Form):
    email = forms.EmailField(label='Email')
    come_from = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):

        # we need this woodoo magick to allow
        # multiple email fields in the form
        if 'data' in kwargs:
            data = kwargs['data']
            data._mutable = True
            data.setlist('email', filter(None, data.getlist('email')))
            data._mutable = False
        super(SubscriptionForm, self).__init__(*args, **kwargs)


class SubscribedView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/subscribed.html'

    def get_context_data(self, **kwargs):
        result = super(SubscribedView, self).get_context_data(**kwargs)

        # if we know from which landing user came
        # we'll set it into the context to throw
        # this value into the Google Analytics and
        # Yandex Metrika
        landing = self.request.GET.get('from')
        if landing:
            result.setdefault('tracked_vars', {})
            result['tracked_vars']['landing'] = landing

        return result


class HumansView(TemplateView):
    template_name = 'allmychanges/humans.txt'
    content_type = 'text/plain'


from django.core.cache import cache



def get_package_data_for_template(changelog,
                                  filter_args,
                                  limit_versions,
                                  after_date,
                                  code_version='v1',
                                  ordering=None,
                                  show_unreleased=True):
    name = changelog.name
    namespace = changelog.namespace

    versions = []
    versions_queryset = changelog.versions.filter(**filter_args)
    # this allows to reduce number of queries in 5 times

    if ordering:
        # if we are in this branch, then we probably
        # rendering PackageView
        versions_queryset = versions_queryset.order_by(*ordering)
        versions_queryset = versions_queryset[:limit_versions]
        # now we'll pop up any unreleased versions
        normal_versions = []
        unreleased_versions = []
        for idx, version in enumerate(versions_queryset):
            if version.unreleased:
                unreleased_versions.append(version)
            else:
                normal_versions.append(version)

        if show_unreleased:
            versions_queryset = unreleased_versions + normal_versions
        else:
            # we need this to hide unreleased versions from screenshots
            versions_queryset = normal_versions
    else:
        versions_queryset = versions_queryset[:limit_versions]

    for version in versions_queryset:
        if after_date is not None and version.date is not None \
           and version.date < after_date.date():
            show_discovered_as_well = True
        else:
            show_discovered_as_well = False

        versions.append(dict(id=version.id,
                             number=version.number,
                             date=version.date,
                             discovered_at=version.discovered_at.date(),
                             last_seen_at=version.last_seen_at,
                             show_discovered_as_well=show_discovered_as_well,
                             filename=version.filename,
                             processed_text=version.processed_text,
                             unreleased=version.unreleased,
                             tweet_id=version.tweet_id))

    latest_version = changelog.latest_version() \
                     if isinstance(changelog, Changelog) else None

    result = dict(namespace=namespace,
                  name=name,
                  description=getattr(changelog, 'description', ''),
                  source=changelog.source,
                  show_itunes_badge='itunes.apple.com' in changelog.source,
                  changelog=dict(
                      id=changelog.id,
                      updated_at=changelog.updated_at,
                      next_update_at=getattr(changelog, 'next_update_at', None),
                      problem=changelog.problem,
                      obj=changelog,
                      tweet_id=latest_version.tweet_id if latest_version else None,
                  ),
                  versions=versions)
    return result


def get_digest_for(changelogs,
                   before_date=None,
                   after_date=None,
                   limit_versions=5,
                   code_version='v1'):
    """Before date and after date are inclusive."""
    # search packages which have changes after given date

    # we exclude unreleased changes from digest
    # because they are not interesting
    # probably we should make it a user preference
    filter_args = {'unreleased': False,
                   'code_version': code_version,
                   'preview_id': None}

    if before_date and after_date:
        filter_args['discovered_at__range'] = (after_date, before_date)
    else:
        if before_date:
            filter_args['discovered_at__lt'] = before_date
        if after_date:
            filter_args['discovered_at__gte'] = after_date

    changelogs = changelogs.filter(**{'versions__' + key: value
                                    for key, value in filter_args.items()})
    changelogs = changelogs.distinct()

    changes = [get_package_data_for_template(
        changelog, filter_args, limit_versions,
        after_date, code_version)
               for changelog in changelogs]

    return changes


class CachedMixin(object):
    def get(self, *args, **kwargs):
        cache_key, cache_ttl = self.get_cache_params(*args, **kwargs)
        response = cache.get(cache_key)
        if response is None:
            response = super(CachedMixin, self).get(*args, **kwargs)
            response.render()
            cache.set(cache_key, response, cache_ttl)
        return response

    def get_cache_params(self, *args, **kwargs):
        """This method should return cache key and value TTL."""
        raise NotImplementedError('Please, implement get_cache_params method.')


class DigestView(LoginRequiredMixin, CachedMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/digest.html'

    def get_cache_params(self, *args, **kwargs):
        user = self.request.user

        code_version = self.request.GET.get('code_version', 'v2')
        cache_key = 'digest-{username}-{packages}-{changes}-{code_version}'.format(
            username=user.username,
            packages=user.changelogs.count(),
            changes=Version.objects.filter(changelog__trackers=user).count(),
            code_version=code_version)

        if self.request.GET:
            cache_key += ':'
            cache_key += ':'.join('{0}={1}'.format(*item)
                                  for item in self.request.GET.items())
        return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)
        result['menu_digest'] = True

        now = timezone.now()
        one_day = datetime.timedelta(1)
        day_ago = now - one_day
        week_ago = now - datetime.timedelta(7)
        month_ago = now - datetime.timedelta(31)
        code_version = self.request.GET.get('code_version', 'v2')

        result['code_version'] = code_version
        result['current_user'] = self.request.user


        changelogs = self.request.user.changelogs

        result['today_changes'] = get_digest_for(changelogs,
                                                 after_date=day_ago,
                                                 code_version=code_version)
        result['week_changes'] = get_digest_for(changelogs,
                                                before_date=day_ago,
                                                after_date=week_ago,
                                                code_version=code_version)
        result['month_changes'] = get_digest_for(changelogs,
                                                 before_date=week_ago,
                                                 after_date=month_ago,
                                                 code_version=code_version)
        result['ealier_changes'] = get_digest_for(changelogs,
                                                  before_date=month_ago,
                                                  code_version=code_version)

        result['no_packages'] = changelogs \
                                 .exclude(namespace='web', name='allmychanges') \
                                 .count() == 0
        result['no_data'] = all(
            len(result[key]) == 0
            for key in result.keys()
            if key.endswith('_changes'))

        return result

    def get(self, *args, **kwargs):
        chat.send('User {0} trying to view a digest'.format(self.request.user.username),
                  channel='tasks')
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'digest-view',
                             'User viewed the digest')
        return super(DigestView, self).get(*args, **kwargs)


class LandingDigestView(CachedMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/landing-digest.html'

    def get_cache_params(self, *args, **kwargs):
        changelogs = self.request.GET.get('changelogs', '')
        self.changelogs = parse_ints(changelogs)

        # this parameter is used in ios-promo because
        # many apps are really old and we need to show
        # something for them
        self.long_period = self.request.GET.get('long-period', '')

        cache_key = 'digest-{changelogs}'.format(changelogs=join_ints(changelogs))

        if self.long_period:
            # don't cache for ios-promo
            return cache_key + '-long', 0
        else:
            return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(LandingDigestView, self).get_context_data(**kwargs)
        now = timezone.now()
        one_day = datetime.timedelta(1)
        day_ago = now - one_day
        week_ago = now - datetime.timedelta(7)
        code_version = self.request.GET.get('code_version', 'v2')

        result['code_version'] = code_version
        result['current_user'] = self.request.user

        changelogs = Changelog.objects.filter(pk__in=self.changelogs)

        if self.long_period:
            changelog_statuses = {ch.status for ch in changelogs}
            if 'processing' not in changelog_statuses:
                # we only return results if all changelogs are ready
                result['long_changes'] = get_digest_for(
                    changelogs,
                    after_date=now - datetime.timedelta(365 * 5),
                    code_version=code_version)
        else:
            result['today_changes'] = get_digest_for(
                changelogs,
                after_date=day_ago,
                code_version=code_version)
            result['week_changes'] = get_digest_for(
                changelogs,
                before_date=day_ago,
                after_date=week_ago,
                code_version=code_version)
        return result

    def get(self, *args, **kwargs):
        # here, we remember user's choice in a cookie, to
        # save these changelogs into his tracking list after login
        response = super(LandingDigestView, self).get(*args, **kwargs)
        response.set_cookie('tracked-changelogs', join_ints(self.changelogs))
        return response


class PackageSelectorVersionsView(CachedMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/landing-versions.html'

    def get_cache_params(self, *args, **kwargs):
        changelog = self.request.GET.get('changelog')
        self.changelog = int(changelog)
        cache_key = 'landing-versions-{changelog}'.format(changelog=changelog)
        return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(PackageSelectorVersionsView, self).get_context_data(**kwargs)
        changelog = Changelog.objects.get(pk=self.changelog)
        versions = list(changelog.latest_versions(3))

        result['package'] = dict(
            namespace=changelog.namespace,
            name=changelog.name,
            versions=versions)
        return result

    def get(self, *args, **kwargs):
        response = super(PackageSelectorVersionsView, self).get(*args, **kwargs)
        return response


class LoginView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/login.html'

    def get_context_data(self, **kwargs):
        result = super(LoginView, self).get_context_data(**kwargs)
        result['next'] = self.request.GET.get('next', reverse('digest'))
        return result

    def get(self, request, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('digest'))
        return super(LoginView, self).get(request, **kwargs)


class PackageView(CommonContextMixin, LastModifiedMixin, TemplateView):
    def get_template_names(self):
        if self.request.GET.get('snap'):
            return 'allmychanges/package-snap.html'
        return 'allmychanges/package.html'

    def last_modified(self, *args, **kwargs):
        discovered_versions = Version.objects.filter(
            changelog__namespace=kwargs['namespace'],
            changelog__name=kwargs['name']).order_by('-discovered_at')
        latest = list(discovered_versions[:1].values_list('discovered_at', flat=True))
        if latest:
            return latest[0]

    def get_context_data(self, **kwargs):
        result = super(PackageView, self).get_context_data(**kwargs)

        code_version = self.request.GET.get('code_version', 'v2')
        result['code_version'] = code_version

        if self.request.user.is_authenticated() and self.request.user.username == 'svetlyak40wt':
            result['show_sources'] = True
            result['show_issues'] = True
        else:
            result['show_sources'] = self.request.GET.get('show_sources', None)

        filter_args = {'code_version': code_version}

        changelog = get_object_or_404(
            Changelog.objects.prefetch_related('versions'),
            namespace=kwargs['namespace'],
            name=kwargs['name'])

        already_tracked = False
        if self.request.user.is_authenticated():
            login_to_track = False
            already_tracked = self.request.user.does_track(changelog)
        else:
            login_to_track = True
            already_tracked = False

        package_data = get_package_data_for_template(
            changelog,
            filter_args,
            100,
            None,
            code_version=code_version,
            ordering=('-order_idx',),
            show_unreleased=not self.request.GET.get('snap'))

        result['package'] = package_data
        result['login_to_track'] = login_to_track
        result['already_tracked'] = already_tracked
        result['issues'] = changelog.issues.filter(resolved_at=None)
        result['num_trackers'] = changelog.trackers.count()

        # twitter card
        if self.request.META.get('HTTP_USER_AGENT', '').lower().startswith('twitterbot'):
            # with open('static/shots/55a4a1916a5b747a15f5e43a5128f9e9f2abafd3.png', 'rb') as f:
            #     from requests_oauthlib import OAuth1
            #     auth = OAuth1('MqSwRY2fa3PC8rA8XrWmvBgcw', 'MAa8BU031BHCREoGOxNo8m8FvBm5Hj6D7zdVoHwQxnZHw632C5',
            #                   '7148262-pv9vR4JJp76vmRL5Yn8XDG3mHYTOz0vLTMGTslY28K', 'OAg3N5mGSfPOX9U2juHz9xV1JtL6VDPoaDinU89sQwF75')
            #     response = requests.post(
            #         'https://upload.twitter.com/1.1/media/upload.json',
            #         auth=auth,
            #         files={'media': ('screenshot.png', f.read(), 'image/png')})
            #     image_url = response.json()['media_id_string']

            print 'Showing card to twitter bot'
            image_url = self.request.build_absolute_uri(self.request.path) + 'snap/'
#            image_url = 'https://pbs.twimg.com/media/CFG4AwSUgAAU0eH.jpg'
#            image_url = 'https://pbs.twimg.com/media/CFG3i1hWIAA6WbT.png'
#            image_url = 'http://media.svetlyak.ru/gallery/120830/03-34-01.jpg'
            twitter = dict(card='summary_large_image',
                           site='@allmychanges',
                           title=changelog.name + "'s release notes.",
                           description=changelog.description if changelog.description else 'Latest versions of ' + changelog.name,
                           image=image_url)
            # twitter = dict(card='photo',
            #                site='@allmychanges',
            #                title=changelog.name + "'s release notes.",
            #                image=image_url)
            # twitter['image:width'] = 600
            # twitter['image:height'] = 232
            result['twitter_card'] = twitter

        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'package-view',
                             u'User opened changelog:{0}'.format(changelog.pk))
        return result


class BadgeView(View):
    def get(self, *args, **kwargs):
        changelog = get_object_or_404(
            Changelog.objects.prefetch_related('versions'),
            namespace=kwargs['namespace'],
            name=kwargs['name'])

        version = changelog.latest_version()
        if version is not None:
            version = version.number
        else:
            version = '?.?.?'

        # replacing to dash because repl.ca uses minus as a separator
        version = version.replace(u'-', u'–')
        url = u'https://img.shields.io/badge/changelog-{0}-brightgreen.svg'.format(
            version)

        content = cache.get(url)

        if content is None:
            r = requests.get(url)
            content = r.content
            cache.set(url, content, HOUR)

        response = HttpResponse(content, content_type='image/svg+xml;charset=utf-8')
        response['Content-Length'] = len(content)
        response['Cache-Control'] = 'no-cache'
        return response



class AfterLoginView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user

        with log.name_and_fields('after-login', username=user.username):
            UserHistoryLog.merge(user, self.request.light_user)
            LightModerator.merge(user, self.request.light_user)
            Issue.merge(user, self.request.light_user)

            if timezone.now() - self.request.user.date_joined < datetime.timedelta(0, 60):
                # if account was registere no more than minute ago, then show
                # user a page where he will be able to correct email
                UserHistoryLog.write(user, self.request.light_user,
                                     action='account-created',
                                     description='User created account')
                response = reverse('account-settings') + '?registration=1#notifications'
            else:
                UserHistoryLog.write(user, self.request.light_user,
                                     action='login',
                                     description='User logged in')
                response = reverse('index')

            tracked_changelogs = parse_ints(self.request.COOKIES.get('tracked-changelogs', ''))
            log.info('Cookie tracked-changelogs={0}'.format(tracked_changelogs))

            if tracked_changelogs:
                log.info('Merging tracked changelogs')

                user_changelogs = {ch.id
                                 for ch in user.changelogs.all()}
                # TODO: this should be updated to work whith new tracking scheme
                for changelog_id in tracked_changelogs:
                    if changelog_id not in user_changelogs:
                        with log.fields(changelog_id=changelog_id):
                            try:
                                changelog = Changelog.objects.get(pk=changelog_id)
                                user.track(changelog)
                            except Exception:
                                log.trace().error('Unable to save landing package')

            skipped_changelogs = parse_ints(self.request.COOKIES.get('skipped-changelogs', ''))
            log.info('Cookie skipped-changelogs={0}'.format(skipped_changelogs))

            if skipped_changelogs:
                log.info('Merging skipped changelogs')

                for changelog_id in skipped_changelogs:
                    with log.fields(changelog_id=changelog_id):
                        try:
                            changelog = Changelog.objects.get(pk=changelog_id)
                            user.skip(changelog)
                        except Exception:
                            log.trace().error('Unable to merge skipped changelog')

        return response

    def dispatch(self, *args, **kwargs):
        response = super(AfterLoginView, self).dispatch(*args, **kwargs)
        # here we nulling a cookie because already merged all data in
        # `get_redirect_url` view
        response.delete_cookie('tracked-changelogs')
        return response


class StyleGuideView(TemplateView):
    template_name = 'allmychanges/style-guide.html'



class LandingView(CommonContextMixin, FormView):
    landings = []
    form_class = SubscriptionForm

    def __init__(self, landings=[], *args, **kwargs):
        self.landings = landings
        super(LandingView, self).__init__(*args, **kwargs)

    def get_template_names(self):
        return 'allmychanges/landings/{0}.html'.format(
            self.landing)

    def get_success_url(self):
        return '/subscribed/?from=' + self.landing

    def get_initial(self):
        return {'come_from': 'landing-' + self.landing}

    def get_context_data(self, **kwargs):
        result = super(LandingView, self).get_context_data(**kwargs)
        result.setdefault('tracked_vars', {})
        result['tracked_vars']['landing'] = self.landing
        return result

    def form_valid(self, form):
        Subscription.objects.create(
            email=form.cleaned_data['email'],
            come_from=form.cleaned_data['come_from'],
            date_created=timezone.now())
        return super(LandingView, self).form_valid(form)

    def get(self, request, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect('/digest/')

        session_key = u'landing:' + request.path

        # for testing purpose, landing name could be
        # supplied as ?landing=some-name GET parameter
        self.landing = request.GET.get('landing')
        if self.landing is None:
            self.landing = request.session.get(session_key)
        else:
            request.session[session_key] = self.landing

        if self.landing not in self.landings:
            self.landing = random.choice(self.landings)
            request.session[session_key] = self.landing

        return super(LandingView, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        come_from = request.POST.get('come_from', '')
        self.landing = come_from.split('-', 1)[-1]
        return super(LandingView, self).post(request, **kwargs)



class RaiseExceptionView(View):
    def get(self, request, **kwargs):
        1/0



class ChangeLogView(View):
    def get(self, *args, **kwargs):
        path = os.path.join(
            os.path.dirname(__file__),
            '..', 'CHANGELOG.md')
        with open(path) as f:
            content = f.read()

        response = HttpResponse(content, content_type='plain/text')
        response['Content-Length'] = len(content)
        return response


class ProfileView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = User
    template_name = 'allmychanges/account-settings.html'

    def get_form_class(self):
        from django.forms.models import modelform_factory
        return modelform_factory(User, fields=('email', 'timezone', 'send_digest', 'slack_url', 'webhook_url'))

    def get_context_data(self, **kwargs):
        result = super(ProfileView, self).get_context_data(**kwargs)
        result['from_registration'] = self.request.GET.get('registration')
        return result

    def get_success_url(self):
        if self.request.POST.get('from_registration'):
            return '/digest/'
        else:
            return '/account/settings/'


    def get_object(self, queryset=None):
        return self.request.user

    def get(self, *args, **kwargs):
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'profile-view',
                             'User opened his profile settings')
        return super(ProfileView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'profile-update',
                             'User saved his profile settings')
        messages.add_message(self.request, messages.INFO, 'Account settings were saved.')
        return super(ProfileView, self).post(*args, **kwargs)


class TokenForm(forms.Form):
    token = forms.CharField(label='Token')



def get_or_create_user_token(user):
    from oauthlib.common import generate_token
    try:
        app_name = 'internal'
        app = Application.objects.get(name=app_name)
    except Application.DoesNotExist:
        app = Application.objects.create(user=User.objects.get(username='svetlyak40wt'),
                                         name=app_name,
                                         client_type=Application.CLIENT_PUBLIC,
                                         authorization_grant_type=Application.GRANT_IMPLICIT)

    try:
        token = AccessToken.objects.get(user=user, application=app)
    except AccessToken.DoesNotExist:
        token = AccessToken.objects.create(
            user=user,
            scope='read write',
            expires=timezone.now() + datetime.timedelta(0, settings.ACCESS_TOKEN_EXPIRE_SECONDS),
            token=generate_token(),
            application=app)

    return token


def delete_user_token(user, token):
    AccessToken.objects.filter(token=token).delete()


class TokenView(LoginRequiredMixin, CommonContextMixin, FormView):
    form_class = TokenForm
    template_name = 'allmychanges/token.html'
    success_url = '/account/token/'

    def get_initial(self):
        token = get_or_create_user_token(self.request.user)
        return {'token': token.token}

    def form_valid(self, form):
        delete_user_token(self.request.user, form.cleaned_data['token'])
        return super(TokenView, self).form_valid(form)


class UserHistoryView(SuperuserRequiredMixin,
                      CommonContextMixin,
                      TemplateView):
    template_name = 'allmychanges/user-history.html'

    def get_context_data(self, **kwargs):
        result = super(UserHistoryView, self).get_context_data(**kwargs)
        user = User.objects.get(username=kwargs['username'])

        heatmap = get_user_actions_heatmap(
            user,
            only_active=self.request.GET.get('all') is None)

        timestamp = lambda dt: arrow.get(dt).timestamp
        grouped = dict((str(timestamp(date)), count) for date, count in heatmap.iteritems())

        result['activity_heat_map'] = grouped

        limit = int(self.request.GET.get('limit', '20'))
        result['log'] = UserHistoryLog.objects \
                                      .filter(user=user) \
                                      .prefetch_related('user') \
                                      .order_by('-id')[:limit]

        def get_changelog_url(match):
            try:
                ch = Changelog.objects.get(pk=match.group('pk'))
                return ch.get_absolute_url()
            except:
                return 'Not Found'

        def process_description(text):
            return re.sub(ur'changelog:(?P<pk>\d+)',
                          get_changelog_url,
                          text)
        for item in result['log']:
            item.description = process_description(item.description)
        return result


class ImmediateResponse(BaseException):
    def __init__(self, response):
        self.response = response


class ImmediateMixin(object):
    def get(self, *args, **kwargs):
        try:
            return super(ImmediateMixin, self).get(*args, **kwargs)
        except ImmediateResponse as e:
            return e.response



class SearchView(ImmediateMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)

        q = self.request.GET.get('q').strip()
        if '/' in q:
            namespace, name = q.split('/', 1)
        elif ' ' in q:
            namespace, name = q.split(' ', 1)
        else:
            namespace = None
            name = q

        params = dict(name=name.strip())
        if namespace:
            params['namespace'] = namespace.strip()

        changelogs = Changelog.objects.filter(**params)
        if changelogs.count() == 1:
            changelog = changelogs[0]
            raise ImmediateResponse(
                HttpResponseRedirect(reverse('package', kwargs=dict(
                    name=changelog.name,
                    namespace=changelog.namespace))))

        if '://' in q:
            # then might be it is a URL?
            normalized_url, _, _ = normalize_url(q, for_checkout=False)
            try:
                changelog = Changelog.objects.get(source=normalized_url)
                if changelog.name is not None:
                    raise ImmediateResponse(
                        HttpResponseRedirect(reverse('package', kwargs=dict(
                            name=changelog.name,
                            namespace=changelog.namespace))))

            except Changelog.DoesNotExist:
                pass

            raise ImmediateResponse(
                    HttpResponseRedirect(reverse('add-new') \
                                         + '?' \
                                         + urllib.urlencode({'url': normalized_url})))

        context.update(params)
        context['changelogs'] = changelogs
        context['q'] = q
        return context


class AddNewView(ImmediateMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/add-new.html'

    def get_context_data(self, **kwargs):
        context = super(AddNewView, self).get_context_data(**kwargs)
        context['menu_add_new'] = True
        user = self.request.user if self.request.user.is_authenticated() else None

        url = self.request.GET.get('url')
        if url is None:
            if 'step3' in self.request.GET:
                context['title'] = 'Step 3 of 3'
                context['step3'] = True
            else:
                context['title'] = 'Add new'
        else:
            normalized_url, _, _ = normalize_url(url, for_checkout=False)

            # first, we'll get params from query, if they were given
            params = dict(name=self.request.GET.get('name'),
                          namespace=self.request.GET.get('namespace'),
                          description=self.request.GET.get('description', ''),
                          icon=self.request.GET.get('icon', ''))

            # and finally, we'll try to guess downloader
            if not params.get('downloader'):
                downloaders = guess_downloaders(normalized_url)

                params['downloader'] = ','.join(
                    d['name'] for d in downloaders)
            else:
                downloaders = []


            # TODO: replace with code inside of downloaders
            # if name was not given, then we'll try to guess it
            # if not params['name']:
            #     guesser = get_namespace_guesser(params['downloader'])
            #     guessed = guesser(normalized_url)
            #     guessed['name'] = Changelog.create_uniq_name(guessed['namespace'],
            #                                                  guessed['name'])
            #     for key, value in guessed.items():
            #         if value:
            #             params[key] = value
            # icon don't saved into the preview yet
            icon = params.pop('icon')

            try:
                changelog = Changelog.objects.get(source=normalized_url)
                if changelog.name is not None:
                    raise ImmediateResponse(
                        HttpResponseRedirect(reverse('package', kwargs=dict(
                            name=changelog.name,
                            namespace=changelog.namespace))))
                UserHistoryLog.write(self.request.user,
                                     self.request.light_user,
                                     'package-create',
                                     u'User created changelog:{0}'.format(changelog.pk))
            except Changelog.DoesNotExist:
                changelog = Changelog.objects.create(
                    source=normalized_url,
                    icon=icon)

                if user:
                    chat.send('Wow, user {0} added new changelog with url: <{1}>'.format(
                        user.username, normalized_url))
                else:
                    chat.send('Wow, light user {0} added new changelog with url: <{1}>'.format(
                        self.request.light_user, normalized_url))

                UserHistoryLog.write(self.request.user,
                                     self.request.light_user,
                                     'package-create',
                                     u'User created changelog:{0}'.format(changelog.pk))

            changelog.problem = None
            changelog.save()

            preview = changelog.create_preview(
                user=user,
                light_user=self.request.light_user,
                **params)

            preview.schedule_update()

            context['changelog'] = changelog
            context['preview'] = preview
            context['can_edit'] = True
            context['downloaders'] = downloaders

            if self.request.user.is_authenticated() and self.request.user.username in settings.ADVANCED_EDITORS:
                context['can_edit_xslt'] = True

        context['mode'] = 'add-new'
        return context


class AddNewView2(AddNewView):
    template_name = 'allmychanges/add-new2.html'


class EditPackageView(ImmediateMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/edit-package.html'

    def get_context_data(self, **kwargs):
        context = super(EditPackageView, self).get_context_data(**kwargs)
        changelog = Changelog.objects.get(namespace=kwargs['namespace'],
                                          name=kwargs['name'])

        preview = changelog.create_preview(
            user=self.request.user if self.request.user.is_authenticated() else None,
            light_user=self.request.light_user)

        if changelog.versions.count() == 0:
            preview.schedule_update()

        context['changelog'] = changelog
        context['preview'] = preview
        context['mode'] = 'edit'
        context['can_edit'] = changelog.editable_by(self.request.user,
                                                    self.request.light_user)

        if self.request.user.is_authenticated() and self.request.user.username in settings.ADVANCED_EDITORS:
            context['can_edit_xslt'] = True

        return context


class EditPackageView2(EditPackageView):
    template_name = 'allmychanges/edit-package2.html'



class PreviewView(CachedMixin, CommonContextMixin, TemplateView):
    """This view is used to preview how changelog will look like
    at "Add New" page.
    It returns an html fragment to be inserted into the "Add new" page.
    """
    template_name = 'allmychanges/changelog-preview.html'

    def get_cache_params(self, *args, **kwargs):
        preview_id = kwargs['pk']
        self.preview = Preview.objects.get(pk=preview_id)

        cache_key = 'changelog-preview-{0}:{1}:{2}'.format(
            self.preview.id,
            int(time.mktime(self.preview.updated_at.timetuple()))
            if self.preview.updated_at is not None
            else 'missing',
            self.preview.get_processing_status())
#        print 'Cache key:', cache_key
        return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(PreviewView, self).get_context_data(**kwargs)
        # initially there is no versions in the preview
        # and we'll show versions from changelog if any exist
        preview = self.preview
        changelog = preview.changelog

        if preview.status == 'created':
            obj = changelog
        else:
            obj = preview

        code_version = 'v2'
        filter_args = {'code_version': code_version}
        if self.preview.updated_at is not None:
            filter_args['preview'] = self.preview
        else:
            filter_args['preview'] = None

        package_data = get_package_data_for_template(
            obj,
            filter_args,
            10,
            None,
            code_version=code_version)

        has_results = len(package_data['versions'])

        if self.preview.status == 'error':
            problem = self.preview.problem
        else:
            if self.preview.status == 'success' and not has_results:
                problem = 'Unable to find changelog.'
            else:
                problem = None

        result['package'] = package_data
        result['has_results'] = has_results
        result['problem'] = problem
        result['show_sources'] = True

        HUMANIZED = {
            'waiting-in-the-queue': 'Waiting in the queue.',
            'downloading': 'Downloading sources.',
            'searching-versions': 'Searching versions.',
            'processing-vcs-history': 'Processing VCS history.',
            'updating-database': 'Updating database.',
        }
        status = self.preview.get_processing_status()
        result['processing_status'] = HUMANIZED.get(status, status)
        return result

    def post(self, *args, **kwargs):
        preview = Preview.objects.get(pk=kwargs['pk'])

        def parse_list(text):
            for line in re.split(r'[\n,]', text):
                yield line.strip()

        if preview.light_user == self.request.light_user or (
                self.request.user.is_authenticated() and
                self.request.user == preview.user):
            data = anyjson.deserialize(self.request.read())

            preview.set_search_list(
                parse_list(data.get('search_list', '')))
            preview.set_ignore_list(
                parse_list(data.get('ignore_list', '')))
            preview.xslt = data.get('xslt', '')

            if preview.source != data.get('source'):
                preview.downloader = None

            preview.source = data.get('source')
            preview.downloader = data.get('downloader')
            preview.set_status('processing')
            preview.save()
            preview.schedule_update()

        return HttpResponse('ok')


class IndexView(CommonContextMixin, TemplateView):
    def get_context_data(self, **kwargs):
        result = super(IndexView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            UserHistoryLog.write(self.request.user,
                                 self.request.light_user,
                                 'index-view',
                                 'User opened an index page.')
        else:
            UserHistoryLog.write(self.request.user,
                                 self.request.light_user,
                                 'landing-digest-view',
                                 'User opened a landing page with digest.')
        return result

    def get_template_names(self):
        if self.request.user.is_authenticated():
            return ['allmychanges/login-index.html']

        return ['allmychanges/new-index.html']


class IssuesFilterForm(forms.Form):
    page_size = forms.IntegerField(required=False)
    namespace = forms.CharField(required=False)
    name = forms.CharField(required=False)
    type = forms.CharField(required=False)


class IssuesView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/issues.html'

    def get_context_data(self, **kwargs):
        result = super(IssuesView, self).get_context_data(**kwargs)
        queryset = Issue.objects.order_by('-id')

        if 'resolved' in self.request.GET:
            queryset = queryset.exclude(resolved_at=None)
            result['title'] = 'Resolved issues'
        else:
            queryset = queryset.filter(resolved_at=None)
            result['title'] = 'Issues'

        form = IssuesFilterForm(self.request.GET)

        if form.is_valid():
            page_size = form.cleaned_data['page_size'] or 20


            if form.cleaned_data['namespace']:
                result['show_back_button'] = True
                queryset = queryset.filter(changelog__namespace=form.cleaned_data['namespace'])
            if form.cleaned_data['name']:
                queryset = queryset.filter(changelog__name=form.cleaned_data['name'])
            if form.cleaned_data['type']:
                result['show_back_button'] = True
                queryset = queryset.filter(type=form.cleaned_data['type'])

        result['total_issues'] = queryset.count()
        result['issues'] = queryset[:page_size]
        url = self.request.build_absolute_uri()
        if not '?' in url:
            url += '?'
        else:
            url += '&'
        result['current_url'] = url
        return result


class IssueDetailView(CommonContextMixin, DetailView):
    template_name = 'allmychanges/issue.html'
    model = Issue


import arrow
#import tablib

from allmychanges.models import User, ACTIVE_USER_ACTIONS


def get_cohort_users(date, span_months):
    return User.objects.filter(date_joined__range=
                               (date.date(), date.replace(months=span_months).date()))

def expand_weeks(start, end):
    date = start
    while date < end:
        yield date
        date = date.replace(days=7)

def get_cohort_stats(start_from, cohort):
    """Возвращает новый словарь, добавляя к когорте поле data.
    При этом data, это словарик, содержащий число активных пользователей
    из этой когорты в прошедших неделях. Отсчет идет с даты start_from.
    """
    stats = []
    today = arrow.utcnow()
    cohort_starts_at = cohort['date']

    date = start_from
    while date < today:
        next_date = date.replace(days=7)
        if date >= cohort_starts_at:
            active_users = cohort['users'].filter(
                history_log__action__in=ACTIVE_USER_ACTIONS,
                history_log__created_at__range=(
                    date.date(), next_date.date())) \
                                          .distinct().count()
        else:
            active_users = None
        stats.append(active_users)
        date = next_date
    return dict(cohort, data=stats)


class AdminDashboardView(SuperuserRequiredMixin,
                         CommonContextMixin,
                         TemplateView):
    template_name = 'allmychanges/admin-dashboard.html'

    def get_context_data(self, **kwargs):
        result = super(AdminDashboardView, self).get_context_data(**kwargs)
        result['title'] = 'Admin Dashboard'

        # default period is two weeks
        period = int(self.request.GET.get('period', 14))
        period = timezone.now() - datetime.timedelta(period)

        users = list(User.objects \
                    .filter(date_joined__gte=period) \
                    .order_by('-date_joined') \
                    .annotate(num_changelogs=Count('changelogs')))
        for user in users:
            user.auth_providers = user.social_auth.all().values_list('provider', flat=True)
        result['users'] = users

        # calculating cohorts for retention graphs
        now = arrow.utcnow()
        start_date = arrow.get(2014, 1, 1)
        span_months = 3
        all_dates = arrow.Arrow.range('month', start_date, now)
        cohort_dates = all_dates[::span_months]
        cohorts = [{'date': date,
                    'name': date.format('YYYY-MM-DD'),
                    'span': span_months,
                    'users': get_cohort_users(date, span_months)}
                   for date in cohort_dates]

        stats = map(lambda cohort: get_cohort_stats(start_date, cohort),
                    cohorts)

        stats = [dict(data=item['data'], name=item['name'])
                 for item in stats]
        result['data'] = anyjson.serialize(stats)

        # для отображения роста и потерь аудитории
        from allmychanges import churn
        churn_labels, churn_data = churn.get_graph_data(
            now.replace(months=-12), now)
        result['churn_data'] = anyjson.serialize(churn_data)
        result['churn_labels'] = anyjson.serialize(
            [arrow.get(date).format('YYYY-MM-DD')
             for date in churn_labels])
        return result


class FirstStepForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', 'timezone']


class FirstStepView(LoginRequiredMixin, CommonContextMixin, UpdateView):
    model = User
    template_name = 'allmychanges/first-steps/first.html'
    success_url = '/first-steps/2/'

    def get_form_class(self):
        return FirstStepForm

    def get_object(self, queryset=None):
        return self.request.user

    def get(self, *args, **kwargs):
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'first-step-view',
                             'User opened first step of the wizard')
        return super(FirstStepView, self).get(*args, **kwargs)

    def form_valid(self, *args, **kwargs):
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'first-step-post',
                             'User pressed Next button on the first step page')
        response = super(FirstStepView, self).form_valid(*args, **kwargs)

        user = self.request.user
        code = EmailVerificationCode.new_code_for(user)
        send_email(recipient=user.email,
                   subject='Please, confirm your email',
                   template='verify-email.html',
                   context=dict(
                       user=user,
                       hash=code.hash))
        return response


class VerifyEmail(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/verify-email.html'

    def get_context_data(self, *args, **kwargs):
        result = super(VerifyEmail, self).get_context_data(**kwargs)
        code = EmailVerificationCode.objects.get(hash=kwargs['code'])
        user = code.user
        user.email_is_valid = True
        user.save(update_fields=('email_is_valid',))

        UserHistoryLog.write(user,
                             self.request.light_user,
                             'verify-email',
                             'User has verified his email')
        return result


class SecondStepView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/first-steps/second.html'


class HelpView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/help.html'

    def get_context_data(self, *args, **kwargs):
        result = super(HelpView, self).get_context_data(**kwargs)
        topic = self.kwargs['topic'].strip('/') or 'index'
        filename = os.path.join(settings.PROJECT_ROOT, 'help/', topic + '.md')

        if not os.path.exists(filename):
            raise Http404

        with open(filename) as f:
            html = markdown2.markdown(f.read())
            result['content'] = html

        if topic == 'faq':
            result['menu_faq'] = True
        else:
            result['menu_help'] = True
        return result


_browser = None
_browser_lock = threading.Lock()


class RenderView(View):
    permanent = False

    def get(self, request):
        global _browser

        url = request.build_absolute_uri(request.path[:-5]) + '?snap=yes'
        if 'version' in request.GET:
            url += '&version=' + request.GET['version']

        with log.name_and_fields('renderer', url=url):
            log.info('Snapshot for url was requested')

            filename = sha1(url).hexdigest() + '.png'
            full_path = os.path.join(settings.SNAPSHOTS_ROOT, filename)
            # redirect_url = request.build_absolute_uri(
            #     os.path.join(settings.SNAPSHOTS_URL, filename))

            if not os.path.exists(full_path):
                subprocess.check_call([settings.PROJECT_ROOT + '/makescreenshot',
                                       '--width', '590',
                                       '--height', '600',
                                       url,
                                       full_path])
                # with _browser_lock:
                #     if _browser is None:
                #         log.info('Creating browser instance')
                #         from allmychanges.browser import Browser
                #         _browser = Browser()
                #     log.info('Creating snapshot')
                #     _browser.save_image(url, full_path, width=480)

        with open(full_path, 'rb') as f:
            content = f.read()

        response = HttpResponse(content, content_type='image/png')
        response['Content-Length'] = len(content)
        return response


class SleepView(RedirectView):
    permanent = False

    def get_redirect_url(self):
        log.info('TEST SLEEP for 30 secs')
        time.sleep(30)
        log.info('TEST SLEEP for 30 secs DONE')
        return '/sleep/'


class TrackListView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/track-list.html'

    def get_context_data(self, **kwargs):
        context = super(TrackListView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            changelogs = list(self.request.user.changelogs.exclude(name=None).order_by('namespace', 'name'))
        else:
            changelogs = []
        context['changelogs'] = changelogs
        if len(changelogs) <= 7:
            namespaces = sorted(set(ch.namespace for ch in changelogs))
            context['suggest_namespaces'] = namespaces
        return context


class RssFeedView(View):
    def get(self, *args, **kwargs):
        rss_hash = kwargs.get('feed_hash')
        if rss_hash:
            user = get_object_or_404(User, rss_hash=rss_hash)
            versions = Version.objects \
                              .filter(changelog__trackers=user) \
                              .exclude(unreleased=True) \
                              .order_by('-discovered_at')
        else:
            raise Http404

        current_url = self.request.build_absolute_uri(self.request.get_full_path())

        from feedgen.feed import FeedGenerator
        fg = FeedGenerator()
        fg.id(current_url)
        fg.title('New Release Notes')
        fg.author({'name':'AllMyChanges.com','email':'support@allmychanges.com'})
        fg.link(href=self.request.build_absolute_uri('/'), rel='alternate' )
        fg.logo('https://allmychanges.com/static/allmychanges/img/logo/48x48.png')
        fg.subtitle('Fresh news from the opensource world')

        fg.link(href=current_url, rel='self')
        fg.language('en')

        for version in versions[:20]:
            ch = version.changelog
            fe = fg.add_entry()
            version_url = self.request.build_absolute_uri(ch.get_absolute_url()) + '#' + version.number

            fe.id(version_url)
            fe.link(href=version_url, rel='alternate')
            fe.pubdate(arrow.get(version.date or version.discovered_at).datetime)
            fe.title(u'{0}/{1} {2}'.format(
                ch.namespace, ch.name, version.number))
            fe.content(version.processed_text)


        content = fg.rss_str(pretty=True)

        response = HttpResponse(content, content_type='application/rss+xml;charset=utf-8')
        response['Cache-Control'] = 'no-cache'
        return response


class CategoryView(CachedMixin, CommonContextMixin, TemplateView):
    """List packages in selected categories.
    """
    template_name = 'allmychanges/category.html'

    def get_cache_params(self, *args, **kwargs):
        return 'category-view1-' + kwargs.get('category'), 0

    def get_context_data(self, *args, **kwargs):
        result = super(CategoryView, self).get_context_data(**kwargs)
        category = kwargs['category']
        changelogs = Changelog.objects.only_active().filter(namespace=category)
        result.update({
            'changelogs': changelogs,
            'menu_catalogue': True,
            'category': category})
        return result


class CategoriesView(CachedMixin, CommonContextMixin, TemplateView):
    """View all categories as a sorted list
    """
    template_name = 'allmychanges/categories.html'

    def get_cache_params(self, *args, **kwargs):
        return 'categories-view', 0

    def get_context_data(self, *args, **kwargs):
        result = super(CategoriesView, self).get_context_data(**kwargs)
        categories = sorted(set(Changelog.objects.only_active().values_list('namespace', flat=True)))
        categories = groupby(categories, lambda item: item[0])
        categories = [(letter, list(names))
                      for letter, names in categories]

        result['categories'] = categories
        result['menu_catalogue'] = True

        if 'step3' in self.request.GET:
            result['title'] = 'Step 3 of 3'
        else:
            result['title'] = 'All Categories'
        return result
