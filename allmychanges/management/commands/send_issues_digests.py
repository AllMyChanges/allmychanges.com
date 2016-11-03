# coding: utf-8
import logging

from optparse import make_option
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from django.contrib.auth import get_user_model
from allmychanges.notifications.email import send_email


def prepare_digest_for(user):
    data = []
    total = 0

    for changelog in user.moderated_changelogs.all():
        unresolved = list(
            changelog.issues.filter(resolved_at=None).order_by('-importance')
        )

        if unresolved:
            data.append(dict(changelog=changelog,
                             issues=unresolved))
            total += len(unresolved)

    return total, data


def send_digest_to(user, debug=False):
    """Отправляет пользователю дайжест проблем с модерируемыми им
    проектами на AllMyChanges.
    """

    total, data = prepare_digest_for(user)
    subject = 'There are some issues at AllMyChanges'

    in_beta = True
    if in_beta:
        email = 'svetlyak.40wt+issue-digests@gmail.com'
        subject = subject + ' (for ' + user.username + ')'
    else:
        email = user.email

    send_email(email,
               subject,
               'issues-digest.html',
               context=dict(
                   issues_count=total,
                   data=data,
               ),
               tags=['allmychanges', 'issues-digest'],
               debug=debug)


class Command(LogMixin, BaseCommand):
    help = u"""Prepares and sends digests to all users."""
    period = 'day'
    option_list = BaseCommand.option_list + (
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=False,
                    help='Write html into local "./emails" folder.'),
    )
    def handle(self, debug=False, *args, **kwargs):
        # this will disable cssutil's logger
        cssutils_logger = logging.getLogger('CSSUTILS')
        cssutils_logger.level = logging.ERROR

        users = get_user_model().objects.exclude(email=None)
        for user in users:
            send_digest_to(user, debug=debug)
