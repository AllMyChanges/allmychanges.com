from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        sources = args[1:]
        changelog = Changelog.objects.get(name=name)
        changelog.versions.filter(
            filename__in=sources).delete()
