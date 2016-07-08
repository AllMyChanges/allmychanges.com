# coding: utf-8
from pprint import pprint
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.downloaders import guess_downloaders


class Command(LogMixin, BaseCommand):
    help = u"""Command to test how downloader guesser workds for given url."""

    def add_arguments(self, parser):
        # Positional arguments
        # Moredocumentation is available here:
        # https://docs.djangoproject.com/en/1.9/howto/custom-management-commands/#accepting-optional-arguments
        parser.add_argument('url')


    def handle(self, url, **options):
        for guessed in guess_downloaders(url):
            print 'Downloader:', guessed['name']
            print 'Changelog params:'
            pprint(guessed['changelog'])
            print 'Downloader params:'
            pprint(guessed['params'])
            print '\n'
