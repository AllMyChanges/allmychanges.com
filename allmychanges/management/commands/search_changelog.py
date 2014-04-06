# coding: utf-8
from django.core.management.base import BaseCommand
from allmychanges.utils import search_changelog2


class Command(BaseCommand):
    help = u"""Search file which probably contains changelog"""

    def handle(self, *args, **options):
        path = args[0] if args else '.'
        filename, raw_data = search_changelog2(path)

        if filename:
            print filename, len(raw_data)
        else:
            print 'not found'

