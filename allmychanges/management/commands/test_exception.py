from django.core.management.base import NoArgsCommand
from twiggy_goodies.django import LogMixin


class Command(LogMixin, NoArgsCommand):
    help = u"""A command to test logging."""

    def handle_noargs(self, **options):
        1/0
