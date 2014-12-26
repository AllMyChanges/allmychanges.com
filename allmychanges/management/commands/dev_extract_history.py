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
                                        write_vcs_versions_slowly)


class Command(LogMixin, BaseCommand):
    help = u"""Command to test VCS log extractors' first step — dates and messages extraction."""
    option_list = BaseCommand.option_list + (
        # make_option('--limit',
        #             type='int',
        #             help='Limit history to N latest commits'),
        make_option('--full',
                    action='store_true',
                    dest='full',
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
        # extract_version = choose_version_extractor(path)
        # write_vcs_versions_slowly(commits, extract_version)
        commits = get_history(path, limit=options.get('limit_history', 0))

        if options['bumps']:
            extract_version = choose_version_extractor(path)
            write_vcs_versions_slowly(commits, extract_version)
            bumps = mark_version_bumps(commits)
            for bump in bumps:
                print bump, commits[bump]['version']
        else:
            for commit in commits:
                print commit
        # bumps = mark_version_bumps(commits)
        # grouped = group_versions(commits, bumps)

        # fork_points = defaultdict(int)
        # for commit in commits.values():
        #     for parent in commit['parents']:
        #         fork_points[parent] += 1

        # fork_points = dict((hash, [num_childs, 0])
        #                    for hash, num_childs in fork_points.items()
        #                    if num_childs > 1)

        # write_vcs_versions_slowly(commits, extract_version)

        # def rec(commit, left_lines=0, right_lines=0):
        #     hash = commit['hash']
        #     if hash in fork_points:
        #         pass
        #     print '{0}*{1} "{2}"'.format(
        #         '| ' * left_lines,
        #         '| ' * right_lines,
        #         commit['message'].split('\n', 1)[0])

        #     num_parents = len(commit['parents'])
        #     if num_parents > 1:
        #         print '|' + '\\' * (num_parents - 1)

        #     for idx, parent in enumerate(reversed(commit['parents'])):
        #         try:
        #             parent_commit = commits[parent]
        #         except KeyError:
        #             print 'History done'
        #             break

        #         rec(parent_commit,
        #             left_lines + num_parents - idx - 1,
        #             right_lines + idx - 1)

        # rec(commits['root'])




        # if options['limit']:
        #     commits = commits[-options['limit']:]
        # if options['full']:
        #     write_vcs_versions_slowly(commits, extract_version)
        # else:
        #     write_vcs_versions_bin(commits, extract_version)

        # for commit in commits:
        #     print commit['date'], commit['hash'], commit['version']
        #     for line in commit['message'].split('\n'):
        #         print '\t>', line
