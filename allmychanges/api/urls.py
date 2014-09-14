# -*- coding: utf-8 -*-
from rest_framework_extensions.routers \
    import ExtendedDefaultRouter as DefaultRouter

from allmychanges.api.views import (
    RepoViewSet,
    SubscriptionViewSet,
    AutocompleteNamespaceView,
    AutocompletePackageNameView,
    SearchAutocompleteView,
    LandingPackageSuggestView,
    MessagesView,
    ChangelogViewSet,
    VersionViewSet,
    ValidateChangelogName)
#    PackageViewSet)


router = DefaultRouter()
router.root_view_name = 'main-api-path'
router.register(r'repos', RepoViewSet, base_name='repo')
router.register(r'subscriptions', SubscriptionViewSet, base_name='repo')
#xrouter.register(r'packages', PackageViewSet, base_name='package')
router.register(r'versions', VersionViewSet, base_name='version')
router.register(r'changelogs', ChangelogViewSet, base_name='changelog')
router.register(r'messages', MessagesView, base_name='messages')
router.register(r'autocomplete-namespaces', AutocompleteNamespaceView, base_name='autocomplete-namespaces')
router.register(r'autocomplete-package-name', AutocompletePackageNameView, base_name='autocomplete-package-name')
router.register(r'search-autocomplete', SearchAutocompleteView, base_name='search-autocomplete')
router.register(r'landing-package-suggest', LandingPackageSuggestView, base_name='landing-package-suggest')
router.register(r'validate-changelog-name', ValidateChangelogName.as_view(), base_name='validate-changelog-name')


#urlpatterns = router.urls

from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url('', include(router.urls)),
    url(r'^validate-changelog-name/$', ValidateChangelogName.as_view(), name='validate-changelog-name')
)
