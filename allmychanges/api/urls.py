# -*- coding: utf-8 -*-
from rest_framework_extensions.routers \
    import ExtendedDefaultRouter as DefaultRouter

from allmychanges.api.views import (
    SubscriptionViewSet,
    AutocompleteNamespaceView,
    AutocompletePackageNameView,
    SearchAutocompleteView,
    LandingPackageSuggestView,
    MessagesView,
    ChangelogViewSet,
    PreviewViewSet,
    VersionViewSet,
    IssueViewSet,
    ValidateChangelogName)


router = DefaultRouter()
router.root_view_name = 'main-api-path'
router.register(r'subscriptions', SubscriptionViewSet, base_name='repo')
router.register(r'versions', VersionViewSet, base_name='version')
router.register(r'changelogs', ChangelogViewSet, base_name='changelog')
router.register(r'previews', PreviewViewSet, base_name='preview')
router.register(r'issues', IssueViewSet, base_name='issues')
router.register(r'messages', MessagesView, base_name='messages')
router.register(r'autocomplete-namespaces', AutocompleteNamespaceView, base_name='autocomplete-namespaces')
router.register(r'autocomplete-package-name', AutocompletePackageNameView, base_name='autocomplete-package-name')
router.register(r'search-autocomplete', SearchAutocompleteView, base_name='search-autocomplete')
router.register(r'landing-package-suggest', LandingPackageSuggestView, base_name='landing-package-suggest')
router.register(r'validate-changelog-name', ValidateChangelogName, base_name='validate-changelog-name')


urlpatterns = router.urls
