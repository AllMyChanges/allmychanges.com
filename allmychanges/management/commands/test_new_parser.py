from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.parsing import pipeline


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        graphite_send(release=1)
