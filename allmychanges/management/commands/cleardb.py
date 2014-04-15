from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Repo


class Command(LogMixin, BaseCommand):
    help = u"""Deletes all repositories and related information."""

    def handle(self, *args, **options):
        Repo.objects.all().delete()
