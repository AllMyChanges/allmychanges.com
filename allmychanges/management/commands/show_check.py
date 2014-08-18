from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Package


class Command(LogMixin, BaseCommand):
    help = u"""Show check list of given package"""

    def handle(self, package, *args, **options):
        package = Package.objects.get(name=package)
        changelog = package.changelog
        check_list = changelog.get_check_list()

        def process(check):
            if check[1]:
                return u':'.join(check)
            else:
                check[0]

        print u'\n'.join(map(process, check_list)).encode('utf-8')
