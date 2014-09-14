from django.core.urlresolvers import reverse
from django.contrib.sitemaps import Sitemap
from .models import Changelog


class PackagesSitemap(Sitemap):
    changefreq = 'daily'

    def items(self):
        return [log for log in Changelog.objects.exclude(name=None)
                if log.latest_version() is not None]

    def lastmod(self, obj):
        version = obj.latest_version()
        return version.discovered_at

    def location(self, obj):
        url = reverse('package', kwargs=dict(
            name=obj.name,
            namespace=obj.namespace))
        return url
