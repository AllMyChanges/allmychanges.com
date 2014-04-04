from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from .views import (IndexView,
                    HumansView,
                    DigestView,
                    EditDigestView,
                    PackageView)
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect


urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),

    url(r'^digest/$', DigestView.as_view(), name='digest'),
    url(r'^digest/edit/$', EditDigestView.as_view(), name='edit-digest'),
    
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='package'),
    
    url(r'^humans.txt/$', HumansView.as_view(), name='humans'),
    url(r'^v1/', include('allmychanges.api.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon.ico/$', lambda x: redirect('/static/favicon.ico')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'logout/', 'django.contrib.auth.views.logout', name='logout'),
    url(r'', include('social_auth.urls')),
)

urlpatterns += staticfiles_urlpatterns()
