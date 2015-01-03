# coding: utf-8
import envoy
import os

from optparse import make_option
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.utils import cd
from allmychanges.vcs_extractor import (choose_history_extractor,
                                        choose_version_extractor,
                                        mark_version_bumps,
                                        write_vcs_versions_slowly,
                                        write_vcs_versions_fast)


class Command(LogMixin, BaseCommand):
    help = u"""Command to test VCS log extractors' first step — dates and messages extraction."""
    option_list = BaseCommand.option_list + (
        # make_option('--limit',
        #             type='int',
        #             help='Limit history to N latest commits'),
        make_option('--slow',
                    action='store_true',
                    dest='slow',
                    default=False,
                    help='Extract version for every commit'),
        make_option('--bumps',
                    action='store_true',
                    dest='bumps',
                    default=False,
                    help='Show hashes where version bump was found.'),
        make_option('--stop-at-hash',
                    help='Stop when a version assigned to a given commit.'),
        make_option('--limit-history',
                    type='int',
                    help='Number of commits to gather.'))

    def handle(self, *args, **options):
        path = args[0] if args else '.'

        if options['stop_at_hash']:
            os.environ['STOP_AT_HASH'] = options['stop_at_hash']

        with cd(path):
            envoy.run('git pull')

        get_history = choose_history_extractor(path)
        commits = get_history(path, limit=options.get('limit_history', 0))

        if options['bumps']:
            extract_version = choose_version_extractor(path)

            num_extractions = [0]
            def custom_extractor(path):
                num_extractions[0] += 1
                return extract_version(path)

            if options['slow']:
                write_vcs_versions_slowly(commits, custom_extractor)
            else:
                write_vcs_versions_fast(commits, custom_extractor)

            bumps = mark_version_bumps(commits)
            for bump in bumps:
                print bump, commits[bump]['version']

            print 'Num commits:', len(commits) - 1
            print 'Num version extractions:', num_extractions[0]
        else:
            for commit in commits:
                print commit
