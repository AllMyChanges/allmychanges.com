from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from .views import (OldIndexView,
                    IndexView,
                    UserHistoryView,
                    HumansView,
                    DigestView,
                    EditDigestView,
                    LandingDigestView,
                    BadgeView,
                    AfterLoginView,
                    LoginView,
                    SubscribedView,
                    StyleGuideView,
                    LandingView,
                    RaiseExceptionView,
                    ChangeLogView,
                    ProfileView,
                    TokenView,
                    PackageView)
from .sitemaps import PackagesSitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from django.views.generic.base import TemplateView


sitemaps = {'packages': PackagesSitemap}

urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^sitemap\.xml$',
         'django.contrib.sitemaps.views.sitemap',
         {'sitemaps': sitemaps}),

    url(r'^robots\.txt$',
         TemplateView.as_view(template_name='robots.txt')),

    # TODO REMOVE THESE TWO
    url(r'^old-index/$', OldIndexView.as_view(), name='old-index'),
    url(r'^coming-soon/$', LandingView.as_view(landings=['coming-soon']), name='comint-soon'),

    url(r'^subscribed/$', SubscribedView.as_view(), name='subscribed'),

    url(r'^digest/$', DigestView.as_view(), name='digest'),
    url(r'^landing-digest/$', LandingDigestView.as_view(), name='landing-digest'),
    url(r'^digest/edit/$', EditDigestView.as_view(), name='edit-digest'),
    
    url(r'^u/(?P<username>.*?)/history/', UserHistoryView.as_view(), name='user-history'),
    url(r'^u/(?P<username>.*?)/(?P<namespace>.*?)/(?P<name>.*?)/badge/$', BadgeView.as_view(), name='badge'),
    url(r'^u/(?P<username>.*?)/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='package'),

    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/badge/$', BadgeView.as_view(), name='badge'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='package-canonical'),


    url(r'^humans.txt/$', HumansView.as_view(), name='humans'),
    url(r'^v1/', include('allmychanges.api.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon.ico/$', lambda x: redirect('/static/favicon.ico')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^logout/', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^after-login/', AfterLoginView.as_view(), name='after-login'),
    url(r'^style-guide/', StyleGuideView.as_view(), name='style-guide'),
    url(r'^landing/ru/', LandingView.as_view(landings=['ru1-green', 'ru1-red']), name='landing-ru'),
    url(r'^landing/en/', LandingView.as_view(landings=['en1-green']), name='landing-en'),
    url(r'^account/settings/$', ProfileView.as_view(), name='account-settings'),
    url(r'^account/token/', TokenView.as_view(), name='token'),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),
    url(r'^raise-exception/', RaiseExceptionView.as_view(), name='raise-exception'),
    url(r'^CHANGELOG.md$', ChangeLogView.as_view(), name='CHANGELOG.md'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
)

urlpatterns += staticfiles_urlpatterns()
