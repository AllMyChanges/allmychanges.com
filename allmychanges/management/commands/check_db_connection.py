import traceback

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from django.conf import settings
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Send stats to graphite Graphite."""
    requires_system_checks = False


    def handle(self, *args, **options):
        for name in sorted(dir(settings)):
            print name, '=', getattr(settings, name)

        try:
            changelogs = Changelog.objects.all()
            print 'Num changelogs:', len(changelogs)
        except Exception:
            traceback.print_exc()
