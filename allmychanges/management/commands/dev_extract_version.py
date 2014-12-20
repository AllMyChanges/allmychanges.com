# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.vcs_extractor import choose_version_extractor


class Command(LogMixin, BaseCommand):
    help = u"""Command to test VCS log extractors' second step — version extraction."""

    def handle(self, *args, **options):
        path = args[0] if args else '.'

        get_version = choose_version_extractor(path)
        print get_version(path, use_threads=False)
