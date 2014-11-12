# -*- coding: utf-8 -*-
import datetime
import anyjson
import time
import random
import requests
import os
import urllib
import re

from braces.views import LoginRequiredMixin
from django.views.generic import (TemplateView,
                                  RedirectView,
                                  FormView,
                                  UpdateView,
                                  View)
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from twiggy_goodies.threading import log

from allmychanges.models import (Package,
                                 LightModerator,
                                 Subscription,
                                 Changelog,
                                 User,
                                 UserHistoryLog,
                                 Preview,
                                 Item)
from oauth2_provider.models import Application, AccessToken

from allmychanges.utils import (HOUR,
                                parse_ints,
                                join_ints)
from allmychanges.downloader import normalize_url
from allmychanges.tasks import update_preview_task


class CommonContextMixin(object):
    def get_context_data(self, **kwargs):
        result = super(CommonContextMixin, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request

        key = 'num_tracked_changelogs'
        num_tracked_changelogs = cache.get(key)
        if num_tracked_changelogs is None:
            num_tracked_changelogs = Changelog.objects.count()
            cache.set(key, num_tracked_changelogs, HOUR)
        result[key] = num_tracked_changelogs

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



def get_package_data_for_template(package_or_changelog, filter_args, limit_versions, after_date, code_version='v1'):
    name = package_or_changelog.name
    namespace = package_or_changelog.namespace

    if isinstance(package_or_changelog, Package):
        changelog = package_or_changelog.changelog
        user = package_or_changelog.user
    else:
        changelog = package_or_changelog
        user = None

    versions = []
    versions_queryset = changelog.versions.filter(**filter_args)

    # this allows to reduce number of queries in 5 times
    versions_queryset = versions_queryset.prefetch_related('sections__items')

    for version in versions_queryset[:limit_versions]:
        sections = []
        for section in version.sections.all():
            sections.append(dict(notes=section.notes,
                                 items=[
                                     dict(text=item.text,
                                          type=item.type)
                                     for item in section.items.all()]))
        if after_date is not None and version.date is not None \
           and version.date < after_date.date():
            show_discovered_as_well = True
        else:
            show_discovered_as_well = False

        versions.append(dict(number=version.number,
                             date=version.date,
                             discovered_at=version.discovered_at.date(),
                             show_discovered_as_well=show_discovered_as_well,
                             filename=version.filename,
                             sections=sections,
                             unreleased=version.unreleased))

    return dict(namespace=namespace,
                name=name,
                source=changelog.source,
                user=dict(
                    username=user.username if user else None,
                ),
                changelog=dict(
                    id=changelog.id,
                    updated_at=changelog.updated_at,
                    next_update_at=changelog.next_update_at,
                    filename=changelog.filename,
                    problem=changelog.problem,
                ),
                versions=versions)


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
            changes=Item.objects.filter(section__version__changelog__trackers=user).count(),
            code_version=code_version)

        if self.request.GET:
            cache_key += ':'
            cache_key += ':'.join('{0}={1}'.format(*item)
                                  for item in self.request.GET.items())
        return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)

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

        cache_key = 'digest-{changelogs}'.format(changelogs=join_ints(changelogs))
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
        result['today_changes'] = get_digest_for(changelogs,
                                                 after_date=day_ago,
                                                 code_version=code_version)
        result['week_changes'] = get_digest_for(changelogs,
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


class PackageView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/package.html'

    def get_context_data(self, **kwargs):
        result = super(PackageView, self).get_context_data(**kwargs)

        code_version = self.request.GET.get('code_version', 'v2')
        result['code_version'] = code_version

        result['show_sources'] = self.request.GET.get('show_sources', None)

        filter_args = {'code_version': code_version, 'preview_id': None}

        changelog = None

        changelog = get_object_or_404(
            Changelog.objects.prefetch_related('versions__sections__items'),
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
            code_version=code_version)

        result['package'] = package_data
        result['login_to_track'] = login_to_track
        result['already_tracked'] = already_tracked
        return result

    def get(self, *args, **kwargs):
        UserHistoryLog.write(self.request.user,
                             self.request.light_user,
                             'package-view',
                             u'User opened package ' + self.request.path)
        return super(PackageView, self).get(*args, **kwargs)


class BadgeView(View):
    def get(self, *args, **kwargs):

        if 'username' in kwargs:
            package_or_changelog = get_object_or_404(
                Package.objects.select_related('changelog') \
                              .prefetch_related('changelog__versions__sections__items'),
                user=get_user_model().objects.get(username=kwargs['username']),
                namespace=kwargs['namespace'],
                name=kwargs['name'])
        else:
            package_or_changelog = get_object_or_404(
                Changelog.objects.prefetch_related('versions__sections__items'),
                namespace=kwargs['namespace'],
                name=kwargs['name'])

        version = package_or_changelog.latest_version()
        if version is not None:
            version = version.number
        else:
            version = '?.?.?'

        url = 'http://b.repl.ca/v1/changelog-{0}-brightgreen.png'.format(
            version)

        content = cache.get(url)

        if content is None:
            r = requests.get(url)
            content = r.content
            cache.set(url, content, HOUR)

        response = HttpResponse(content, content_type='image/png')
        response['Content-Length'] = len(content)
        response['Cache-Control'] = 'no-cache'
        return response



class AfterLoginView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user

        with log.name_and_fields('after-login', username=user.username):
            UserHistoryLog.merge(user, self.request.light_user)
            LightModerator.merge(user, self.request.light_user)

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
                response = reverse('digest')

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
    success_url = '/account/settings/'

    def get_form_class(self):
        from django.forms.models import modelform_factory
        return modelform_factory(User, fields=('email', 'timezone'))

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


class TokenView(CommonContextMixin, FormView):
    form_class = TokenForm
    template_name = 'allmychanges/token.html'
    success_url = '/account/token/'

    def get_initial(self):
        token = get_or_create_user_token(self.request.user)
        return {'token': token.token}

    def form_valid(self, form):
        delete_user_token(self.request.user, form.cleaned_data['token'])
        return super(TokenView, self).form_valid(form)


class UserHistoryView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/user-history.html'

    def get_context_data(self, **kwargs):
        result = super(UserHistoryView, self).get_context_data(**kwargs)

        if 'username' in kwargs:
            user = User.objects.get(username=kwargs['username'])
            result['log'] = UserHistoryLog.objects.filter(user=user)
        else:
            user = self.request.user
            user = user if user.is_authenticated() else None

            result['log'] = UserHistoryLog.objects.filter(
                Q(user=user) | Q(light_user=self.request.light_user))
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
        url = self.request.GET.get('url')
        if url is None:
            return Http404

        normalized_url, _, _ = normalize_url(url, for_checkout=False)

        try:
            changelog = Changelog.objects.get(source=normalized_url)
            if changelog.name is not None:
                raise ImmediateResponse(
                    HttpResponseRedirect(reverse('package', kwargs=dict(
                        name=changelog.name,
                        namespace=changelog.namespace))))
        except Changelog.DoesNotExist:
            changelog = Changelog.objects.create(source=normalized_url)

        changelog.problem = None
        changelog.save()


        preview = changelog.previews.create(
            source=changelog.source,
            user=self.request.user if self.request.user.is_authenticated() else None,
            light_user=self.request.light_user)

        update_preview_task.delay(preview.id)

        context['changelog'] = changelog
        context['preview'] = preview
        context['mode'] = 'add-new'
        context['can_edit'] = True
        return context



class EditPackageView(ImmediateMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/edit-package.html'

    def get_context_data(self, **kwargs):
        context = super(EditPackageView, self).get_context_data(**kwargs)
        changelog = Changelog.objects.get(namespace=kwargs['namespace'],
                                          name=kwargs['name'])

        preview = changelog.previews.create(
            source=changelog.source,
            ignore_list=changelog.ignore_list,
            check_list=changelog.check_list,
            user=self.request.user if self.request.user.is_authenticated() else None,
            light_user=self.request.light_user)

        def attrs_to_copy(obj, exclude=()):
            exclude_fields = set(exclude)
            exclude_fields.add('id')
            return {f.name: getattr(obj, f.name)
                    for f in obj.__class__._meta.fields
                    if f.name not in exclude_fields}

        context['changelog'] = changelog
        context['preview'] = preview
        context['mode'] = 'edit'
        context['can_edit'] = changelog.editable_by(self.request.user,
                                                    self.request.light_user)
        return context



class PreviewView(CachedMixin, CommonContextMixin, TemplateView):
    """This view is used to preview how changelog will look like
    at "Add New" page.
    It returns an html fragment to be inserted into the "Add new" page.
    """
    template_name = 'allmychanges/changelog-preview.html'

    def get_cache_params(self, *args, **kwargs):
        preview_id = kwargs['pk']
        self.preview = Preview.objects.get(pk=preview_id)
        cache_key = 'changelog-preview-{0}:{1}'.format(
            self.preview.id,
            int(time.mktime(self.preview.updated_at.timetuple()))
            if self.preview.updated_at is not None
            else 'missing')
        return cache_key, 4 * HOUR

    def get_context_data(self, **kwargs):
        result = super(PreviewView, self).get_context_data(**kwargs)

        # initially there is no versions in the preview
        # and we'll show versions from changelog if any exist
        if self.preview.updated_at is None:
            obj = self.preview.changelog
        else:
            obj = self.preview

        code_version = 'v2'
        filter_args = {'code_version': code_version}
        if self.preview.updated_at is not None:
            filter_args['preview'] = self.preview

        changelog = self.preview.changelog
        package_data = get_package_data_for_template(
            changelog,
            filter_args,
            10,
            None,
            code_version=code_version)

        has_results = obj.versions.filter(code_version=code_version).count() > 0
        has_another_version_results = obj.versions.exclude(code_version=code_version).count() > 0

        if obj.problem:
            problem = obj.problem
        elif not has_results and has_another_version_results:
            problem = 'Unable to find changelog.'
        else:
            problem = None

        result['package'] = package_data
        result['has_results'] = has_results
        result['problem'] = problem
        result['show_sources'] = True
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

            preview.set_check_list(
                parse_list(data.get('search_list', '')))
            preview.set_ignore_list(
                parse_list(data.get('ignore_list', '')))
            preview.source = data.get('source')

            preview.versions.all().delete()
            preview.updated_at = timezone.now()
            preview.save()

            update_preview_task.delay(preview.pk)

        return HttpResponse('ok')



class ToolsView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/tools.html'



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
