# coding: utf-8

import sys

from optparse import make_option
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Issue, User


class Command(LogMixin, BaseCommand):
    help = u"""Resolves issues of given type."""
    option_list = BaseCommand.option_list + (
        make_option('--limit',
                    type='int',
                    help='Resolve no more than N issues'),
        make_option('--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='Just print what will be done'),
        make_option('--type',
                    dest='issue_type',
                    help='Resolve issues of this type.'),
    )

    def handle(self,
               issue_type=None,
               dry_run=False,
               limit=None,
               **kwargs):

        # get all unresolved issues, sorted_by creation date
        # from oldest to newest
        issues = Issue.objects \
                      .filter(resolved_at=None) \
                      .order_by('created_at')

        if issue_type:
            issues = issues.filter(type=issue_type)

            if limit:
                issues = issues[:limit]

            if issues.count() == 0:
                print 'There is no versions to resolve'
                sys.exit(1)

        else:
            # we don't want to resolve all issues by mistake
            # so just output all possible issue types
            types = issues.values_list('type', flat=True)
            types = tuple(sorted(set(types)))

            if not types:
                print 'There is no versions to resolve'
            else:
                print 'Please, specify one of these types:', ', '.join(types)
            sys.exit(2)

        by_user = User.objects.get(username='svetlyak40wt')

        if dry_run:
            print 'These issues will be resolved:'

        for issue in issues:
            if dry_run:
                print repr(issue)
            else:
                issue.resolve(by_user, notify=False)
