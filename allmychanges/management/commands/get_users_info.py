# coding: utf-8
from django.core.management.base import BaseCommand
from django.template.defaultfilters import timesince
from twiggy_goodies.django import LogMixin

from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Drops user and all his packages."""

    def handle(self, *args, **options):
        for user in User.objects.order_by('-id'):
            print user.username
            print '\tJoined:', timesince(user.date_joined) + ' ago'
            print '\tEmail:', user.email
            packages = list(user.changelogs.all())

            if packages:
                print '\tPackages:'
                for changelog in user.changelogs.all():
                    print '\t\t', changelog.namespace, changelog.name, '(http://allmychanges.com' + changelog.get_absolute_url() + ')'
            else:
                print '\tPackages: NO'

            print ''
