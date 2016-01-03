# coding: utf-8

import os
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings

from twiggy_goodies.threading import log
from twiggy_goodies.django import LogMixin
from allmychanges.downloaders import guess_downloaders
from allmychanges.models import (
    Issue)
from allmychanges.utils import (
    update_fields)
from tqdm import tqdm


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
        issues = Issue.objects.filter(resolved_at__isnull=True)

        def calculate_weight(issue):
            pass

        for issue in tqdm(issues):
            calculate_weight(issue)
