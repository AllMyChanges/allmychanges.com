# coding: utf-8
import requests
import sys

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.parsing.postprocessors import sed


class Command(LogMixin, BaseCommand):
    help = u"""Command to test sed rules on given URL.
    Give rules on STDIN and file's URL as first argument."""

    def add_arguments(self, parser):
        parser.add_argument('url')
        parser.add_argument('rule')

    def handle(self, url, rule, *args, **options):
        transform = sed(rule)
        text = requests.get(url).text
        processed = transform(text)
        lines = processed.split('\n')
        processed = u'\n'.join(lines[:20])
        print processed.encode('utf-8')
