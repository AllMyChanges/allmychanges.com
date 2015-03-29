# coding: utf-8
import requests

from re import findall
from itertools import count, islice
from string import strip, ascii_uppercase
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from twiggy_goodies.django import LogMixin
from twiggy_goodies.threading import log
from allmychanges.models import AppStoreUrl


def get_app_store_urls():
    """Returns an iterable which goes through all
    AppStore.
    """
    index_url = 'https://itunes.apple.com/us/genre/ios/id36?mt=8'
    session = requests.Session()
    fetch_page = session.get

    response = fetch_page(index_url)
    categories = findall(
        ur'"https://itunes.apple.com/us/genre/.*?"',
        response.content)
    categories = {strip(url, '"')
                  for url in categories}

    already_seen = set()
    update_already_seen = already_seen.update

    for category_url in categories:
        for letter in ascii_uppercase:
#            print category_url, letter
            for page in count(1):
                page_url = category_url + \
                           '&letter={0}&page={1}'.format(
                               letter, page)
                page = fetch_page(page_url)
                apps = findall(
                    ur'"https://itunes.apple.com/us/app/.*?"',
                    page.content)
                apps = {strip(url, '"') for url in apps}
                apps = apps - already_seen
                if apps:
                    for url in apps:
                        yield strip(url, '"')
                    update_already_seen(apps)
                else:
                    # we hit the last page
                    break


def update_appstore_urls(with_progress=False, limit=50):
    # documentation on app store's search:
    # https://www.apple.com/itunes/affiliates/resources/documentation/itunes-store-web-service-search-api.html#searchexamples
    # Статья про то, как скачать данные с AppStore и некоторых других Google плеев:
    # http://blog.singhanuvrat.com/tech/crawl-itunes-appstore-to-get-list-of-all-apps
#    AppStoreUrl.objects.all().delete()

    possible_number_of_urls = 1042122
    urls = get_app_store_urls()
    if limit:
        urls = islice(urls, 0, limit)
        possible_number_of_urls = limit

    create = AppStoreUrl.objects.create
    info = log.info
    name_and_fields = log.name_and_fields

    def process_url(source):
        # we need this because autocomplete compares
        # these urls agains Changelog model where sources
        # are normalized
        with name_and_fields('autocomplete.appstore.url-fetcher', source=source):
            info('Processing')
            try:
                create(source=source)
            except IntegrityError:
                pass


    if with_progress:
        from clint.textui import progress
        urls = progress.bar(urls, expected_size=possible_number_of_urls)

    for url in urls:
        process_url(url)


class Command(LogMixin, BaseCommand):
    help = u"""Fetches data for autocomplete from different sources"""

    def handle(self, *args, **options):
        update_appstore_urls(with_progress=True, limit=None)
