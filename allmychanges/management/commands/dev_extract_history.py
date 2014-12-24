# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.vcs_extractor import choose_history_extractor


class Command(LogMixin, BaseCommand):
    help = u"""Command to test VCS log extractors' first step — dates and messages extraction."""

    def handle(self, *args, **options):
        path = args[0] if args else '.'
        extract = choose_history_extractor(path)

        for date, message, checkout in extract(path)[:10]:
            print date, message, checkout()
