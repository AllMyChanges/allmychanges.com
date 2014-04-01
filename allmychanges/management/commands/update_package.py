from django.core.management.base import BaseCommand
from django.conf import settings
from allmychanges.models import Package

class Command(BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        package = Package.objects.get(name=name)
        package.update()
