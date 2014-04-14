# -*- coding: utf-8 -*-
import datetime
import random

from django.views.generic import TemplateView, RedirectView, FormView
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect

from allmychanges.models import Package, Subscription


class CommonContextMixin(object):
    def get_context_data(self, **kwargs):
        result = super(CommonContextMixin, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request
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


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)



from django.core.cache import cache

def get_digest_for(user, before_date=None, after_date=None, limit_versions=5):
    cache_key = 'digest-{username}-{before}-{after}-{limit}'.format(
        username=user.username,
        before=before_date.date() if before_date else 0,
        after=after_date.date() if after_date else 0,
        limit=limit_versions)
    
    changes = cache.get(cache_key)
    if changes is None:
        # search packages which have changes after given date
        packages = user.packages

        if before_date is not None:
            packages = packages.filter(changelog__versions__date__lt=before_date)
        if after_date is not None:
            packages = packages.filter(changelog__versions__date__gte=after_date)

        packages = packages.select_related('changelog').distinct()

        changes = []
        for package in packages:
            versions = []
            versions_queryset = package.changelog.versions.all()
            if before_date is not None:
                versions_queryset = versions_queryset.filter(date__lt=before_date)
            if after_date is not None:
                versions_queryset = versions_queryset.filter(date__gte=after_date)

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
                versions.append(dict(number=version.number,
                                     date=version.date,
                                     sections=sections))
            changes.append(dict(namespace=package.namespace,
                                name=package.name,
                                source=package.source,
                                versions=versions))

        cache.set(cache_key, changes, 60 * 60)
    return changes



class DigestView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/digest.html'

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)

        now = timezone.now()
        day_ago = now - datetime.timedelta(1)
        week_ago = now - datetime.timedelta(7)
        month_ago = now - datetime.timedelta(31)


        result['today_changes'] = get_digest_for(self.request.user,
                                                 after_date=day_ago)
        result['week_changes'] = get_digest_for(self.request.user,
                                                before_date=day_ago,
                                                after_date=week_ago)
        result['month_changes'] = get_digest_for(self.request.user,
                                                 before_date=week_ago,
                                                 after_date=month_ago)
        result['ealier_changes'] = get_digest_for(self.request.user,
                                                  before_date=month_ago)

        result['no_packages'] = self.request.user.packages.count() == 0
        result['no_data'] = all(
            len(result[key]) == 0
            for key in result.keys()
            if key.endswith('_changes'))
        return result


class LoginView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/login.html'

    def get_context_data(self, **kwargs):
        result = super(LoginView, self).get_context_data(**kwargs)
        result['next'] = self.request.GET.get('next', reverse('digest'))
        return result

    def get(self, request, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect('/digest/')
        return super(LoginView, self).get(request, **kwargs)
        

class EditDigestView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/edit_digest.html'


class PackageView(CommonContextMixin, TemplateView):
    template_name = 'allmychanges/package.html'

    def get_context_data(self, **kwargs):
        result = super(PackageView, self).get_context_data(**kwargs)

        # TODO: redirect to login if there is no username in kwargs
        # and request.user is anonymous
        kwargs.setdefault('username', self.request.user.username)
        
        result['package'] = get_object_or_404(
            Package.objects.select_related('changelog') \
                          .prefetch_related('changelog__versions__sections__items'),
            user=get_user_model().objects.get(username=kwargs['username']),
            namespace=kwargs['namespace'],
            name=kwargs['name'])

        return result


class BadgeView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        kwargs.setdefault('username', self.request.user.username)
        
        package = get_object_or_404(
            Package.objects.select_related('changelog') \
                          .prefetch_related('changelog__versions__sections__items'),
            user=get_user_model().objects.get(username=kwargs['username']),
            namespace=kwargs['namespace'],
            name=kwargs['name'])

        version = list(package.changelog.versions.all().order_by('-date')[:1])
        if version:
            version = version[0].number
        else:
            version = '?.?.?'

        return 'http://b.repl.ca/v1/changelog-{0}-brightgreen.png'.format(
            version)


class AfterLoginView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if timezone.now() - self.request.user.date_joined < datetime.timedelta(0, 60):
            # if account was registere no more than minute ago, then show
            # user a page where he will be able to correct email
            return '/check-email/'
        return '/digest/'


class EmailForm(forms.Form):
    email = forms.EmailField(label='Please check if this is email you wish to receive your digest and news to')
                            

class CheckEmailView(LoginRequiredMixin, CommonContextMixin, FormView):
    template_name = 'allmychanges/check-email.html'
    form_class = EmailForm
    success_url = '/digest/edit/'

    def get_initial(self):
        return {'email': self.request.user.email}
        
    def form_valid(self, form):
        self.request.user.email = form.cleaned_data['email']
        self.request.user.save()
        return super(CheckEmailView, self).form_valid(form)


class StyleGuideView(TemplateView):
    template_name = 'allmychanges/style-guide.html'



class LandingView(CommonContextMixin, FormView):
    landings = []
    form_class = SubscriptionForm

    def __init__(self, landings=[], *args, **kwargs):
        self.landings = landings
        super(LandingView, self).__init__(*args, **kwargs)

    def get_template_names(self):
        return self.choosen_template

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
        self.landing = request.session.get(session_key)

        if self.landing not in self.landings:
            self.landing = random.choice(self.landings)
            request.session[session_key] = self.landing
            
        self.choosen_template = 'allmychanges/landings/{0}.html'.format(
            self.landing)

        return super(LandingView, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        come_from = request.POST.get('come_from', '')
        self.landing = come_from.split('-', 1)[-1]
        return super(LandingView, self).post(request, **kwargs)
        
