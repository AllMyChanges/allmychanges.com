# coding: utf-8
import string
import requests

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import AutocompleteData


def fetch_from_app_store():
    AutocompleteData.objects.filter(origin='app-store').delete()

    already_seen = set([])

    for letter in string.ascii_lowercase:
        url = ('https://itunes.apple.com/search?'
               'country=us&media=software'
               '&limit=200&term=') + letter
        response = requests.get(url)
        data = response.json()
        for item in data['results']:
            source = item['trackViewUrl']
            if source not in already_seen:
                already_seen.add(source)

                AutocompleteData.objects.create(
                    origin='app-store',
                    title=u'{0} {1}'.format(
                        item['trackName'],
                        item['sellerName']),
                    source=source,
                    icon=item['artworkUrl60'])



class Command(LogMixin, BaseCommand):
    help = u"""Fetches data for autocomplete from different sources"""

    def handle(self, *args, **options):
        fetch_from_app_store()
