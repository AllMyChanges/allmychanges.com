# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Updates description where it is empty."""

    def handle(self, *args, **options):
        changelogs = Changelog.objects.filter(description='')
        for ch in changelogs:
            ch.update_description_from_source(
                fall_asleep_on_rate_limit=True)
