# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.parsing.pipeline import processing_pipe
from allmychanges.utils import split_filenames




def print_version(version):
    print u'{version} ({filename}, {date})'.format(
        version=version.version,
        filename=version.filename,
        date=getattr(version, 'date', None)).encode('utf-8')

    for section in version.content:
        if isinstance(section, basestring):
            print section
        else:
            for item in section:
                print u'\t[{0[type]}] {0[text]}'.format(item).encode('utf-8')


class Command(LogMixin, BaseCommand):
    help = u"""Search changelog like data in given path on disk."""

    def handle(self, path, *args, **options):
        check_list = ignore_list = []

        if len(args) >= 1:
            check_list = [(name, None)
                          for name in split_filenames(args[0])]
        if len(args) >= 2:
            ignore_list = split_filenames(args[1])

        versions = processing_pipe(path,
                                   ignore_list,
                                   check_list)
        for version in versions:
            print_version(version)
