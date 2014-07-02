from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Package


class Command(LogMixin, BaseCommand):
    help = u"""Adds one or more filenames to package's ignore list."""

    def handle(self, package, *filenames, **options):
        package = Package.objects.get(name=package)
        changelog = package.changelog
        ignore_list = changelog.get_ignore_list()
        ignore_list.extend(filenames)
        changelog.set_ignore_list(ignore_list)
        changelog.save()
