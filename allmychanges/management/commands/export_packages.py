from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Package


class Command(LogMixin, BaseCommand):
    help = u"""Exports packages added by one or more users."""

    def handle(self, *args, **options):
        packages = Package.objects.filter(user__username__in=args).distinct()
        for package in packages:
            print u'; '.join((package.namespace,
                             package.name,
                             package.source))
