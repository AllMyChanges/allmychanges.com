# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.downloaders import guess_downloaders
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""This command should be used once, when we'll
    migrate towards storing of all guessed downloaders
    in a database field."""

    def handle(self, *args, **options):
        for ch in Changelog.objects.all():
            if not ch.downloaders:
                print ('Guessing downloaders for '
                       '{0.namespace}/{0.name} ({0.id})').format(ch)

                ch.downloaders = list(guess_downloaders(ch))
                ch.save(update_fields=('downloaders',))
