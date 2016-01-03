# coding: utf-8
import os

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.downloaders import (
    guess_downloaders,
    get_downloader)


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
        os.environ['DEV_DOWNLOAD'] = 'yes'

        source = args[0]
        if len(args) > 1:
            search_list = [(item, None)
                           for item in args[1].split(',')]
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
