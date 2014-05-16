# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Drops user and all his packages."""

    def handle(self, *args, **options):
        if args:
            User.objects.filter(username__in=args).delete()
        else:
            print '\n'.join(
                u.username
                for u in User.objects.all())
