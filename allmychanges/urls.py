from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from .views import (OldIndexView,
                    HumansView,
                    DigestView,
                    EditDigestView,
                    BadgeView,
                    AfterLoginView,
                    CheckEmailView,
                    LoginView,
                    ComingSoonView,
                    SubscribedView,
                    StyleGuideView,
                    PackageView)
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect


urlpatterns = patterns(
    '',
    url(r'^$', ComingSoonView.as_view(), name='index'),
    url(r'^old-index/$', OldIndexView.as_view(), name='old-index'),

    url(r'^subscribed/$', SubscribedView.as_view(), name='subscribed'),

    url(r'^digest/$', DigestView.as_view(), name='digest'),
    url(r'^digest/edit/$', EditDigestView.as_view(), name='edit-digest'),
    
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='package'),
    url(r'^u/(?P<username>.*?)/(?P<namespace>.*?)/(?P<name>.*?)/badge/$', BadgeView.as_view(), name='badge'),
    url(r'^u/(?P<username>.*?)/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='users-package'),

    
    url(r'^humans.txt/$', HumansView.as_view(), name='humans'),
    url(r'^v1/', include('allmychanges.api.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon.ico/$', lambda x: redirect('/static/favicon.ico')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'logout/', 'django.contrib.auth.views.logout', name='logout'),
    url(r'after-login/', AfterLoginView.as_view(), name='after-login'),
    url(r'check-email/', CheckEmailView.as_view(), name='after-login'),
    url(r'style-guide/', StyleGuideView.as_view(), name='style-guide'),
    url(r'accounts/login/', LoginView.as_view(), name='login'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
)

urlpatterns += staticfiles_urlpatterns()
