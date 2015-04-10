from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Deletes versions with sources which starts with given prefixes."""

    def handle(self, *args, **options):
        name = args[0]
        sources = args[1:]

        changelogs = Changelog.objects.filter(name=name)
        for changelog in changelogs:
            for source in sources:
                changelog.versions.filter(
                    filename__startswith=source).delete()
