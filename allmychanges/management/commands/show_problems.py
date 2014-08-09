import os

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Updates single project."""

    def handle(self, *args, **options):
        changelogs = Changelog.objects.exclude(filename=None)
        for changelog in changelogs:
            old_count = changelog.versions.filter(code_version='v1').count()
            new_count = changelog.versions.filter(code_version='v2').count()
            if old_count > new_count or new_count == 0:
                print ''
                print changelog
                print changelog.packages.all(), 'have problems:', old_count, '!=', new_count
