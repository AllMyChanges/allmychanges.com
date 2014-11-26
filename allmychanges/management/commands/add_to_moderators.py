# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import User, Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
        changelog = Changelog.objects.get(name=args[0])
        usernames = args[1:] if len(args) > 1 else ['svetlyak40wt']
        for username in usernames:
            user = User.objects.get(username=username)
            changelog.add_to_moderators(user)
