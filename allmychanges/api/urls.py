# -*- coding: utf-8 -*-
from rest_framework_extensions.routers \
    import ExtendedDefaultRouter as DefaultRouter

from allmychanges.api.views import (
    RepoViewSet,
    SubscriptionViewSet,
    PackageViewSet)


router = DefaultRouter()
router.root_view_name = 'main_api_path'
router.register(r'repos', RepoViewSet, base_name='repo')
router.register(r'subscriptions', SubscriptionViewSet, base_name='repo')
router.register(r'packages', PackageViewSet, base_name='package')


urlpatterns = router.urls
