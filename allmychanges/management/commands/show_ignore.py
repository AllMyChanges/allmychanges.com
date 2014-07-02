from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Package


class Command(LogMixin, BaseCommand):
    help = u"""Show ignore list of given package"""

    def handle(self, package, *args, **options):
        package = Package.objects.get(name=package)
        changelog = package.changelog
        ignore_list = changelog.get_ignore_list()
        print u'\n'.join(ignore_list).encode('utf-8')
