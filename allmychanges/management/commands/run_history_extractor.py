# coding: utf-8
from django.core.management.base import BaseCommand
from allmychanges.utils import choose_history_extractor


class Command(BaseCommand):
    help = u"""Command to test VCS log extractors' first step — dates and messages extraction."""

    def handle(self, *args, **options):
        path = args[0] if args else '.'
        walk_history = choose_history_extractor(path)

        for date, message in walk_history(path):
            print date, message


