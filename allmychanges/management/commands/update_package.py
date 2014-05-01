from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Package
from allmychanges.tasks import update_changelog_task

class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        package = Package.objects.filter(name=name)[0]
        
        if len(args) > 1 and args[1] == 'full':
            package.changelog.versions.all().delete()

        update_changelog_task(package.changelog.source)
