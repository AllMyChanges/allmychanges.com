from django.core.management.base import BaseCommand
from allmychanges.models import Package
from allmychanges.tasks import update_package

class Command(BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        name = args[0]
        package = Package.objects.get(name=name)
        update_package(package.id)