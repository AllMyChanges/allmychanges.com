# coding: utf-8
from django.core.management.base import BaseCommand
from django.template.defaultfilters import timesince
from twiggy_goodies.django import LogMixin

from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Drops user and all his packages."""

    def handle(self, *args, **options):
        for user in User.objects.all():
            print user.username
            print '\tJoined:', timesince(user.date_joined) + ' ago'
            print '\tEmail:', user.email
            packages = list(user.packages.all())

            if packages:
                print '\tPackages:'
                for package in user.packages.all():
                    print '\t\t', package.namespace, package.name, package.source, '(http://allmychanges.com' + package.get_absolute_url() + ')'
            else:
                print '\tPackages: NO'

            print ''
                
            
