# coding: utf-8
from pprint import pprint
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.downloaders import guess_downloaders


class Command(LogMixin, BaseCommand):
    help = u"""Command to test how downloader guesser workds for given url."""

    def handle(self, *args, **options):
        url = args[0]
        for guessed in guess_downloaders(url):
            print 'Downloader:', guessed['name']
            print 'Changelog params:'
            pprint(guessed['changelog'])
            print 'Downloader params:'
            pprint(guessed['params'])
            print '\n'
