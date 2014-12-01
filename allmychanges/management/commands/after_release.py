from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.utils import graphite_send, slack_send
from plumbum.cmd import git


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        graphite_send(release=1)
        with open('.hash-before-release') as f:
            hash_before_release = f.read().strip()
            current_hash = git['rev-parse', '--short', 'HEAD']().strip()
            changes = git['log', '--format=%h %s', '{0}..{1}'.format(hash_before_release,
                                                                  current_hash)]().strip()
            changes = changes.split(u'\n')
            changes = [u'\t* {1} <https://github.com/svetlyak40wt/allmychanges/commit/{0}|{0}>'.format(
                *item.split(' ', 1))
                       for item in changes]
            changes = u'\n'.join(changes)
            slack_send('Deployed {current_hash}:\n{changes}'.format(
                current_hash=current_hash,
                changes=changes))
