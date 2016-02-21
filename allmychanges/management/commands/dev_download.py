# coding: utf-8
import os

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.downloaders import (
    guess_downloaders,
    get_downloader)


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def add_arguments(self, parser):
        parser.add_argument('url')
        parser.add_argument('--search-list')

    def handle(self, *args, **options):
        os.environ['DEV_DOWNLOAD'] = 'yes'
        source = options.get('url')

        search_list = options.get('search_list')
        if search_list:
            search_list = [(item, None)
                           for item in search_list.split(',')]
        else:
            search_list = []

        if '+' in source:
            downloader_name, source = source.split('+', 1)
        else:
            downloaders = list(guess_downloaders(source))
            if not downloaders:
                print 'Unable to find downloader for', source
                return
            if len(downloaders) > 1:
                print 'Please choose one of downloaders:', \
                    ','.join(d['name'] for d in downloaders)
                return
            downloader_name = downloaders[0]

        downloader = get_downloader(downloader_name)
        print downloader(source, search_list=search_list)
