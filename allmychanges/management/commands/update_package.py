from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        changelog = Changelog.objects.filter(name=name)[0]
        changelog.schedule_update(async=False,
                                  full=len(args) > 1 and args[1] == 'full')
