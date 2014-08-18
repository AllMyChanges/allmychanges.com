from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Package


class Command(LogMixin, BaseCommand):
    help = u"""Adds one or more filenames to package's check list."""

    def handle(self, package, *filenames, **options):
        package = Package.objects.get(name=package)
        changelog = package.changelog
        check_list = changelog.get_check_list()
        
        def process_filename(filename):
            if ':' in filename:
                filename, markup = filename.split(':', 1)
            else:
                markup = None
            return filename, markup
    
        check_list.extend(map(process_filename, filenames))
        changelog.set_check_list(check_list)
        changelog.save()
