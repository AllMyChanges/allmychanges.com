from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        changelog = Changelog.objects.get(name=name)
        sources = {v.filename for v in changelog.versions.all()}
        sources = list(sources)
        sources.sort()
        print u'\n'.join(sources).encode('utf-8')
