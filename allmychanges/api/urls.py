# -*- coding: utf-8 -*-
from rest_framework_extensions.routers \
    import ExtendedDefaultRouter as DefaultRouter

from allmychanges.api.views import (
    RepoViewSet,
    SubscriptionViewSet,
    AutocompleteNamespaceView,
    PackageViewSet)


router = DefaultRouter()
router.root_view_name = 'main_api_path'
router.register(r'repos', RepoViewSet, base_name='repo')
router.register(r'subscriptions', SubscriptionViewSet, base_name='repo')
router.register(r'packages', PackageViewSet, base_name='package')
router.register(r'autocomplete-namespaces', AutocompleteNamespaceView, base_name='autocomplete-namespaces')


urlpatterns = router.urls
