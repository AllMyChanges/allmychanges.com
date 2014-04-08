# -*- coding: utf-8 -*-
import datetime

from django.views.generic import TemplateView, RedirectView, FormView, View
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse

from allmychanges.models import Package


class IndexView(TemplateView):
    template_name = 'allmychanges/index.html'

    def get_context_data(self, **kwargs):
        result = super(IndexView, self).get_context_data(**kwargs)
        result['settings'] = settings
        return result


class HumansView(TemplateView):
    template_name = 'allmychanges/humans.txt'
    content_type = 'text/plain'


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class CommonContextMixin(object):
    def get_context_data(self, **kwargs):
        result = super(CommonContextMixin, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request
        return result


def get_digest_for(user, before_date=None, after_date=None, limit_versions=5):
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
    return changes



class DigestView(LoginRequiredMixin, CommonContextMixin, TemplateView):
    template_name = 'allmychanges/digest.html'

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)

        now = timezone.now()
        day_ago = now - datetime.timedelta(1)
        week_ago = now - datetime.timedelta(7)
        month_ago = now - datetime.timedelta(31)


        if self.request.user.is_authenticated():
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
        return result


class LoginView(TemplateView, CommonContextMixin):
    template_name = 'allmychanges/login.html'

    def get_context_data(self, **kwargs):
        result = super(LoginView, self).get_context_data(**kwargs)
        result['next'] = self.request.GET.get('next', reverse('digest'))
        return result


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


from django import forms

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
