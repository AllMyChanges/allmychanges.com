# coding: utf-8

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.downloaders import guess_downloaders
from allmychanges.models import (
    Changelog)
from allmychanges.utils import (
    update_fields)


def parse_package_name(name):
    if '/' in name:
        namespace, name = name.split('/', 1)
        return dict(namespace=namespace,
                    name=name)
    return dict(name=name)


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
        for name in args:
            print 'Migrating', name
            params = parse_package_name(name)
            ch = Changelog.objects.get(**params)
#            import pdb; pdb.set_trace()

#            if not ch.downloaders:
            downloaders = list(guess_downloaders(ch.source))
            update_fields(ch, downloaders=downloaders)
