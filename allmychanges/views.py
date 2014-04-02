# -*- coding: utf-8 -*-
import datetime

from django.views.generic import TemplateView
from django.conf import settings
from django.utils import timezone


class IndexView(TemplateView):
    template_name = 'allmychanges/index.html'

    def get_context_data(self, **kwargs):
        result = super(IndexView, self).get_context_data(**kwargs)
        result['settings'] = settings
        return result


class HumansView(TemplateView):
    template_name = 'allmychanges/humans.txt'
    content_type = 'text/plain'



def get_digest_for(user, before_date=None, after_date=None, limit_versions=5):
    # search packages which have changes after given date
    packages = user.packages

    if before_date is not None:
        packages = packages.filter(repo__versions__date__lt=before_date)
    if after_date is not None:
        packages = packages.filter(repo__versions__date__gte=after_date)

    packages = packages.distinct()
    changes = []
    for package in packages:
        versions = []
        versions_queryset = package.repo.versions.all()
        if before_date is not None:
            versions_queryset = versions_queryset.filter(date__lt=before_date)
        if after_date is not None:
            versions_queryset = versions_queryset.filter(date__gte=after_date)

        for version in versions_queryset[:limit_versions]:
            items = []
            for item in version.items.all():
                items.append(dict(text=item.text,
                                  changes=[
                                      dict(text=change.text,
                                           type=change.type)
                                      for change in item.changes.all()]))
            versions.append(dict(number=version.name,
                                 date=version.date,
                                 items=items))
        changes.append(dict(namespace=package.namespace,
                            name=package.name,
                            versions=versions))
    return changes



class DigestView(TemplateView):
    template_name = 'allmychanges/digest.html'

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request


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
        return result


class EditDigestView(TemplateView):
    template_name = 'allmychanges/edit_digest.html'

    def get_context_data(self, **kwargs):
        result = super(EditDigestView, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request
        return result
