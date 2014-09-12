# -*- coding: utf-8 -*-
import datetime
import random
import requests
import os

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
from django.http import HttpResponseRedirect, HttpResponse
from twiggy_goodies.threading import log

from allmychanges.models import (Package,
                                 Subscription,
                                 Changelog,
                                 User,
                                 UserHistoryLog,
                                 Item)
from oauth2_provider.models import Application, AccessToken

from allmychanges.utils import HOUR


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


class IndexView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/new-index.html'

    def get_context_data(self, **kwargs):
        result = super(IndexView, self).get_context_data(**kwargs)

        UserHistoryLog.objects.create(light_user=self.request.light_user,
                                      action='landing-digest-view',
                                      description='User opened a landing page with digest.')
        return result

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            return HttpResponseRedirect(reverse('digest'))
        return super(IndexView, self).get(*args, **kwargs)


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
        for section in version.sections.filter(code_version=code_version):
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
                    updated_at=changelog.updated_at,
                    next_update_at=changelog.next_update_at,
                    filename=changelog.filename,
                    problem=changelog.problem,
                ),
                versions=versions)


def get_digest_for(packages,
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
                   'code_version': code_version}

    if before_date and after_date:
        filter_args['discovered_at__range'] = (after_date, before_date)
    else:
        if before_date:
            filter_args['discovered_at__lt'] = before_date
        if after_date:
            filter_args['discovered_at__gte'] = after_date

    if issubclass(packages.model, Package):
        packages = packages.filter(**{'changelog__versions__' + key: value
                                      for key, value in filter_args.items()})
        packages = packages.select_related('changelog').distinct()
    else:
        packages = packages.filter(**{'versions__' + key: value
                                      for key, value in filter_args.items()})
        packages = packages.distinct()

    changes = [get_package_data_for_template(package, filter_args, limit_versions, after_date, code_version)
               for package in packages]

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
        code_version = self.request.GET.get('code_version', 'v1')
        cache_key = 'digest-{username}-{packages}-{changes}-{code_version}'.format(
            username=self.request.user.username,
            packages=self.request.user.packages.count(),
            changes=Item.objects.filter(
                section__version__changelog__packages__user=self.request.user).count(),
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
        code_version = self.request.GET.get('code_version', 'v1')

        result['code_version'] = code_version
        result['current_user'] = self.request.user


        packages = self.request.user.packages
        result['today_changes'] = get_digest_for(packages,
                                                 after_date=day_ago,
                                                 code_version=code_version)
        result['week_changes'] = get_digest_for(packages,
                                                before_date=day_ago,
                                                after_date=week_ago,
                                                code_version=code_version)
        result['month_changes'] = get_digest_for(packages,
                                                 before_date=week_ago,
                                                 after_date=month_ago,
                                                 code_version=code_version)
        result['ealier_changes'] = get_digest_for(packages,
                                                  before_date=month_ago,
                                                  code_version=code_version)

        result['no_packages'] = \
                self.request.user.packages \
                                 .exclude(namespace='web', name='allmychanges') \
                                 .count() == 0
        result['no_data'] = all(
            len(result[key]) == 0
            for key in result.keys()
            if key.endswith('_changes'))

        return result

    def get(self, *args, **kwargs):
        if self.request.user.packages.count() == 0:
            return HttpResponseRedirect(reverse('edit-digest'))
        return super(DigestView, self).get(*args, **kwargs)


class LandingDigestView(CachedMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/landing-digest.html'

    def get_cache_params(self, *args, **kwargs):
        packages = self.request.GET.get('packages', '')
        self.packages = map(int, filter(None, packages.split(',')))

        cache_key = 'digest-{packages}'.format(packages=','.join(map(str, sorted(packages))))
        return cache_key, 4 * HOUR
        
    def get_context_data(self, **kwargs):
        result = super(LandingDigestView, self).get_context_data(**kwargs)

        # packages = self.request.GET.get('packages', '')
        # packages = map(int, filter(None, packages.split(',')))

        now = timezone.now()
        one_day = datetime.timedelta(1)
        day_ago = now - one_day
        week_ago = now - datetime.timedelta(7)
        code_version = self.request.GET.get('code_version', 'v1')

        result['code_version'] = code_version
        result['current_user'] = self.request.user

        packages = Changelog.objects.filter(pk__in=self.packages)
        result['today_changes'] = get_digest_for(packages,
                                                 after_date=day_ago,
                                                 code_version=code_version)
        result['week_changes'] = get_digest_for(packages,
                                                before_date=day_ago,
                                                after_date=week_ago,
                                                code_version=code_version)
        return result

    def get(self, *args, **kwargs):
        # here, we remember user's choice in a cookie, to
        # save these packages into his tracking list after login
        response = super(LandingDigestView, self).get(*args, **kwargs)
        response.set_cookie('landing-packages', ','.join(map(str, self.packages)))
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
        

class EditDigestView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/edit_digest.html'


class PackageView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/package.html'

    def get_context_data(self, **kwargs):
        result = super(PackageView, self).get_context_data(**kwargs)

        code_version = self.request.GET.get('code_version', 'v1')
        result['code_version'] = code_version

        filter_args = {'code_version': code_version}

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
        
        package_data = get_package_data_for_template(
            package_or_changelog,
            filter_args,
            100,
            None,
            code_version=code_version)

        result['package'] = package_data
        return result


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

            landing_packages = self.request.COOKIES.get('landing-packages')
            log.info('Cookie landing-packages={0}'.format(landing_packages))
    
            if landing_packages is not None:
                log.info('Merging landing packages')
                landing_packages = map(int, filter(None, landing_packages.split(',')))
                user_packages = {ch.id
                                 for ch in Changelog.objects.filter(packages__user=user)}
                for package_id in landing_packages:
                    if package_id not in user_packages:
                        with log.fields(package_id=package_id):
                            try:
                                changelog = Changelog.objects.get(pk=package_id)
                                user.packages.create(namespace=changelog.namespace,
                                                     name=changelog.name,
                                                     source=changelog.source,
                                                     changelog=changelog)
                            except Exception:
                                log.trace().error('Unable to save landing package')
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

