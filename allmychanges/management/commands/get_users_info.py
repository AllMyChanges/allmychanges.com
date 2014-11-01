# coding: utf-8
import codecs
import sys

from django.core.management.base import BaseCommand
from django.template.defaultfilters import timesince
from twiggy_goodies.django import LogMixin

from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Drops user and all his packages."""

    def handle(self, *args, **options):
        writer = codecs.getwriter('utf-8')(sys.stdout)
        def prn(text):
            writer.write(text)
            writer.write('\n')

        for user in User.objects.order_by('-id'):
            prn(user.username)
            prn(u'\tJoined: {0} ago'.format(timesince(user.date_joined)))
            prn(u'\tEmail: {0}'.format(user.email))
            packages = list(user.changelogs.all())

            if packages:
                prn('\tPackages:')
                for changelog in user.changelogs.all():
                    prn(u'\t\t{0} {1} (http://allmychanges.com{2})'.format(changelog.namespace,
                                             changelog.name,
                                             changelog.get_absolute_url()))
            else:
                prn('\tPackages: NO')

            prn('')
