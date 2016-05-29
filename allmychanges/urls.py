import re

from django.conf.urls import patterns, include, url

from django.conf import settings
from django.views.generic.base import RedirectView


from .views import (OldIndexView,
                    MergeProjectView,
                    TestSlackView,
                    TestWebhookView,
                    IssuesView,
                    HelpView,
                    TrackListView,
                    TagListView,
                    TaggedProjectsView,
                    RssFeedView,
                    IssueDetailView,
                    SleepView,
                    IndexView,
                    AdminUserProfileView,
                    AdminUserProfileEditView,
                    AdminUnsuccessfulView,
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
                    AdminRetentionView,
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
                    SynonymsView,
                    ProjectIssuesView,
                    ProjectView,
                    DeleteProjectView,
                    PingView,
                    EditProjectView)
from .sitemaps import PackagesSitemap
from django.shortcuts import redirect
from django.views.generic.base import TemplateView


sitemaps = {'packages': PackagesSitemap}

urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^ping/$', PingView.as_view(), name='ping'),
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
    url(r'^first-steps/$',
        RedirectView.as_view(url='/first-steps/1/',
                             permanent=False),
        name='first-steps'),
    url(r'^first-steps/1/$', FirstStepView.as_view(), name='first-step'),
    url(r'^first-steps/2/$', SecondStepView.as_view(), name='second-step'),
    url(r'^verify-email/(?P<code>.*)/$', VerifyEmail.as_view(), name='verify-email'),

    url(r'^subscribed/$', SubscribedView.as_view(), name='subscribed'),

    url(r'^digest/$', DigestView.as_view(), name='digest'),
    url(r'^landing-digest/$', LandingDigestView.as_view(), name='landing-digest'),
    url(r'^package-selector-versions/$', PackageSelectorVersionsView.as_view(), name='package-selector-versions'),
    url(r'^preview/(?P<pk>.*?)/$', PreviewView.as_view(), name='preview'),

    url(r'^issues/$', IssuesView.as_view(), name='issues'),
    url(r'^issues/(?P<pk>.*)/$', IssueDetailView.as_view(), name='issue-detail'),

    url(r'^help/(?P<topic>.*)$', HelpView.as_view(), name='help'),

    url(r'^p/new/$', AddNewView.as_view(), name='add-new'),

    url(r'^p/$', CategoriesView.as_view(), name='categories'),

    # these two urls should go before category view
    # because it has more specifity
    url(r'^p/(?P<pk>\d+)/$',
        ProjectView.as_view(),
        name='project-by-id'),
    url(r'^p/(?P<pk>\d+)/edit/$',
        EditProjectView.as_view(),
        name='edit-project-by-id'),
    url(r'^p/(?P<pk>\d+)/delete/$',
        DeleteProjectView.as_view(),
        name='delete-project'),
    url(r'^p/(?P<category>[^/]+?)/$', CategoryView.as_view(), name='category'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/issues/$',
        ProjectIssuesView.as_view(),
        name='project-issues'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/synonyms/$',
        SynonymsView.as_view(),
        name='synonyms'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/badge/$',
        BadgeView.as_view(),
        name='badge'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/edit/$',
        EditProjectView.as_view(),
        name='edit-package'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/merge/$',
        MergeProjectView.as_view(),
        name='merge-project'),
    url(r'^p/(?P<namespace>.*?)/(?P<name>.*?)/$',
        ProjectView.as_view(),
        name='project'),

    url(r'^humans.txt/$', HumansView.as_view(), name='humans'),
    url(r'^v1/', include('allmychanges.api.urls')),
    url(r'^admin/$', AdminDashboardView.as_view(), name='admin-dashboard'),
    url(r'^admin/retention/$', AdminRetentionView.as_view(), name='admin-retention'),
    url(r'^admin/unsuccessful/$', AdminUnsuccessfulView.as_view(), name='admin-unsuccessful'),
    url(r'^admin/u/(?P<username>.*?)/edit/', AdminUserProfileEditView.as_view(), name='admin-user-profile-edit'),
    url(r'^admin/u/(?P<username>.*?)/', AdminUserProfileView.as_view(), name='admin-user-profile'),

    url(r'^favicon.ico/$', lambda x: redirect('/static/favicon.ico')),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^logout/', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^style-guide/', StyleGuideView.as_view(), name='style-guide'),
    url(r'^landing/ru/', LandingView.as_view(landings=['ru1-green', 'ru1-red']), name='landing-ru'),
    url(r'^landing/en/', LandingView.as_view(landings=['en1-green']), name='landing-en'),
    url(r'^for-ios/', LandingView.as_view(landings=['for-ios1']), name='landing-for-ios'),

    url(r'^account/settings/$', ProfileView.as_view(), name='account-settings'),
    url(r'^account/settings/test-slack/$',
        TestSlackView.as_view(),
        name='test-slack'),
    url(r'^account/settings/test-webhook/$',
        TestWebhookView.as_view(),
        name='test-webhook'),
    url(r'^account/track-list/$', TrackListView.as_view(), name='track-list'),
    url(r'^account/tags/$', TagListView.as_view(), name='tag-list'),
    url(r'^account/tags/(?P<name>.*?)/$',
        TaggedProjectsView.as_view(),
        name='tagged-projects'),
    url(r'^account/token/$', TokenView.as_view(), name='token'),
    url(r'^accounts/login/$', LoginView.as_view(), name='login'),

    url(r'^rss/(?P<feed_hash>.*?)/$', RssFeedView.as_view(), name='rss-feed'),

    url(r'^raise-exception/$', RaiseExceptionView.as_view(), name='raise-exception'),
    url(r'^CHANGELOG.md$', ChangeLogView.as_view(), name='CHANGELOG.md'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
)

if True:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]

from django.contrib.staticfiles.views import serve
pattern = r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/'))
urlpatterns += [url(pattern, serve, kwargs={'insecure': True})]
