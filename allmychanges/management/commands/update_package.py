from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog
from allmychanges.tasks import update_changelog_task


class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        changelog = Changelog.objects.filter(name=name)[0]

        if len(args) > 1 and args[1] == 'full':
            changelog.versions.all().delete()

        changelog.problem = None
        changelog.save()
        update_changelog_task(changelog.source)
