# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Packages with given names."""

    def handle(self, *args, **options):
        if args:
            Changelog.objects.filter(name__in=args).delete()
