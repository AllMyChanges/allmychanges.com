from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

from .views import (OldIndexView,
                    IssuesView,
                    HelpView,
                    TrackListView,
                    RssFeedView,
                    IssueDetailView,
                    SleepView,
                    IndexView,
                    UserHistoryView,
                    HumansView,
                    RenderView,
                    SearchView,
                    DigestView,
                    LandingDigestView,
                    PackageSelectorVersionsView,
                    BadgeView,
                    AfterLoginView,
                    FirstStepView,
                    SecondStepView,
                    VerifyEmail,
                    LoginView,
                    AdminDashboardView,
                    CategoryView,
                    CategoriesView,
                    SubscribedView,
                    StyleGuideView,
                    LandingView,
                    RaiseExceptionView,
                    ChangeLogView,
                    PreviewView,
                    AddNewView,
                    ProfileView,
                    TokenView,
                    PackageView,
                    EditPackageView)
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
         TemplateView.as_view(template_name='robots.txt',
                              content_type='text/plain')),

    url(r'^search/$', SearchView.as_view(), name='search'),
    url(r'^.*/snap/$', RenderView.as_view(), name='snap'),
    url(r'^sleep/$', SleepView.as_view(), name='sleep'),

    # TODO REMOVE THESE TWO
    url(r'^old-index/$', OldIndexView.as_view(), name='old-index'),
    url(r'^coming-soon/$', LandingView.as_view(landings=['coming-soon']), name='comint-soon'),

    url(r'^after-login/', AfterLoginView.as_view(), name='after-login'),
    url(r'^first-steps/$', RedirectView.as_view(url='/first-steps/1/'), name='first-steps'),
    url(r'^first-steps/1/$', FirstStepView.as_view(), name='first-step'),
    url(r'^first-steps/2/$', SecondStepView.as_view(), name='second-step'),
    url(r'^verify-email/(?P<code>.*)/$', VerifyEmail.as_view(), name='verify-email'),

    url(r'^subscribed/$', SubscribedView.as_view(), name='subscribed'),

    url(r'^digest/$', DigestView.as_view(), name='digest'),
    url(r'^landing-digest/$', LandingDigestView.as_view(), name='landing-digest'),
    url(r'^package-selector-versions/$', PackageSelectorVersionsView.as_view(), name='package-selector-versions'),
    url(r'^preview/(?P<pk>.*?)/$', PreviewView.as_view(), name='preview'),

    url(r'^u/(?P<username>.*?)/', UserHistoryView.as_view(), name='user-history'),

    url(r'^issues/$', IssuesView.as_view(), name='issues'),
    url(r'^issues/(?P<pk>.*)/$', IssueDetailView.as_view(), name='issue-detail'),

    url(r'^help/(?P<topic>.*)$', HelpView.as_view(), name='help'),

    url(r'^p/new/$', AddNewView.as_view(), name='add-new'),
    url(r'^p/$', CategoriesView.as_view(), name='categories'),
    url(r'^p/(?P<category>[^/]+?)/$', CategoryView.as_view(), name='category'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/badge/$', BadgeView.as_view(), name='badge'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/edit/$', EditPackageView.as_view(), name='edit-package'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/$', PackageView.as_view(), name='package'),


    url(r'^humans.txt/$', HumansView.as_view(), name='humans'),
    url(r'^v1/', include('allmychanges.api.urls')),
    url(r'^admin/dashboard/$', AdminDashboardView.as_view(), name='admin-dashboard'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^favicon.ico/$', lambda x: redirect('/static/favicon.ico')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^logout/', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^style-guide/', StyleGuideView.as_view(), name='style-guide'),
    url(r'^landing/ru/', LandingView.as_view(landings=['ru1-green', 'ru1-red']), name='landing-ru'),
    url(r'^landing/en/', LandingView.as_view(landings=['en1-green']), name='landing-en'),
    url(r'^for-ios/', LandingView.as_view(landings=['for-ios1']), name='landing-for-ios'),

    url(r'^account/settings/$', ProfileView.as_view(), name='account-settings'),
    url(r'^account/track-list/', TrackListView.as_view(), name='track-list'),
    url(r'^account/token/', TokenView.as_view(), name='token'),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),

    url(r'^rss/(?P<feed_hash>.*?)/', RssFeedView.as_view(), name='rss-feed'),

    url(r'^raise-exception/', RaiseExceptionView.as_view(), name='raise-exception'),
    url(r'^CHANGELOG.md$', ChangeLogView.as_view(), name='CHANGELOG.md'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
)

urlpatterns += staticfiles_urlpatterns()
