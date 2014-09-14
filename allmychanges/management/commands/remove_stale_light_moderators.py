from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import LightModerator


class Command(LogMixin, BaseCommand):
    help = u"""Deletes stale light moderators from the database"""

    def handle(self, *args, **options):
        LightModerator.remove_stale_moderators()
