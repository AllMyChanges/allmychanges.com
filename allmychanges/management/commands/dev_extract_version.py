# coding: utf-8
from optparse import make_option

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.vcs_extractor import choose_version_extractor


class Command(LogMixin, BaseCommand):
    help = u"""Command to test VCS log extractors' second step — version extraction."""
    option_list = BaseCommand.option_list + (
        make_option('--pdb',
                    action='store_true',
                    dest='pdb',
                    default=False,
                    help='Stop before extraction'),
    )

    def handle(self, *args, **options):
        path = args[0] if args else '.'

        get_version = choose_version_extractor(path)
        if options.get('pdb'):
            import pdb; pdb.set_trace()  # DEBUG
        print get_version(path, use_threads=False)
