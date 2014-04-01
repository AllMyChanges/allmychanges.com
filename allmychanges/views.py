# -*- coding: utf-8 -*-
from django.views.generic import TemplateView
from django.conf import settings


class IndexView(TemplateView):
    template_name = 'allmychanges/index.html'

    def get_context_data(self, **kwargs):
        result = super(IndexView, self).get_context_data(**kwargs)
        result['settings'] = settings
        return result


class HumansView(TemplateView):
    template_name = 'allmychanges/humans.txt'
    content_type = 'text/plain'


class DigestView(TemplateView):
    template_name = 'allmychanges/digest.html'

    def get_context_data(self, **kwargs):
        result = super(DigestView, self).get_context_data(**kwargs)
        result['settings'] = settings
        result['request'] = self.request
        return result


class EditDigestView(TemplateView):
    template_name = 'allmychanges/edit_digest.html'

    def get_context_data(self, **kwargs):
        result = super(EditDigestView, self).get_context_data(**kwargs)
        result['settings'] = settings
        return result
