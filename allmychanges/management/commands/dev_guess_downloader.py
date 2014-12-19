# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.downloader import guess_downloader


class Command(LogMixin, BaseCommand):
    help = u"""Command to test how downloader guesser workds for given url."""

    def handle(self, *args, **options):
        url = args[0]
        print guess_downloader(url)
