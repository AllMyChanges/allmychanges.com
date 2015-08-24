# coding: utf-8
import itertools

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from twiggy_goodies.threading import log
from allmychanges.models import AutocompleteData, AutocompleteWord2
from allmychanges.downloaders.utils import normalize_url
from multiprocessing.dummy import Pool


def fetch_from_app_store(with_progress=False, limit=50):
    # documentation on app store's search:
    # https://www.apple.com/itunes/affiliates/resources/documentation/itunes-store-web-service-search-api.html#searchexamples
    # Статья про то, как скачать данные с AppStore и некоторых других Google плеев:
    # http://blog.singhanuvrat.com/tech/crawl-itunes-appstore-to-get-list-of-all-apps
    AutocompleteData.objects.filter(origin='app-store').delete()

    possible_number_of_urls = 1042122
    urls = get_app_store_urls()
    if limit:
        urls = itertools.islice(urls, 0, limit)
        possible_number_of_urls = limit

    def process_url(source):
        # we need this because autocomplete compares
        # these urls agains Changelog model where sources
        # are normalized
        # print '\nprocessing-appstore:', source
        with log.name_and_fields('autocomplete.appstore.fetcher', source=source):
            try:
                log.info('Processing')
                source, username, repo, data = normalize_url(source, return_itunes_data=True)

                if AutocompleteData.objects.filter(
                        source=source).count() == 0:

                    AutocompleteData.objects.create(
                        origin='app-store',
                        title=u'{0} by {1}'.format(
                            data['trackName'],
                            data['sellerName']),
                        source=source,
                        icon=data['artworkUrl60'])
            except:
                log.trace().error('Unable to process')

    pool = Pool(8)
    items = pool.imap_unordered(process_url, urls)
#    items = (process_url(url) for url in urls)

    if with_progress:
        from clint.textui import progress
        items = progress.bar(items, expected_size=possible_number_of_urls)

    for item in items:
        pass
    pool.close()
    pool.join()


import time
from clint.textui import progress

from django.db import transaction

def process():
    start = time.time()
    items = AutocompleteData.objects.all()
    items = progress.bar(items.iterator(), expected_size=items.count(), every=100)
    middle = time.time()

    # idx = 0
    for item in items:
        # idx += 1
        # if idx % 100:
        #     print '.',
        item.add_words2()
    end = time.time()
    return start, middle, end


def process_words2():
    items = AutocompleteData.objects.all().using('server-side')
    items = progress.bar(items.iterator(), expected_size=items.count(), every=100)
    for item in items:
        item2 = AutocompleteData.objects.using('default').get(pk=item.pk)
        title = item2.title.split(u' by ', 1)[0]
        title = title.replace(' ', '').lower()[:40]
        word, created = AutocompleteWord2.objects.get_or_create(word=title)
        item2.words2.add(word)

def process_duplicates():
    items = AutocompleteData.objects.all().using('server-side')
    items = progress.bar(items.iterator(), expected_size=items.count(), every=100)

    seen = set()
    ids_to_remove = []
    for item in items:
        if item.source in seen:
            ids_to_remove.append(item.id)
        else:
            seen.add(item.source)

    while ids_to_remove:
        ids = ids_to_remove[-100:]
        ids_to_remove = ids_to_remove[:-100]
        AutocompleteData.objects.filter(pk__in=ids).delete()


class Command(LogMixin, BaseCommand):
    help = u"""Fetches data for autocomplete from different sources"""

    def handle(self, *args, **options):
        process_duplicates()
        return
        # import cProfile, pstats, StringIO
        # pr = cProfile.Profile()
        # pr.enable()

#        fetch_from_app_store(with_progress=True, limit=None)

        # pr.disable()
        # s = StringIO.StringIO()
        # sortby = 'cumulative'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # print s.getvalue()
