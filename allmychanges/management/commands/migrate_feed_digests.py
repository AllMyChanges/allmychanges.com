# coding: utf-8

import datetime

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import User, FeedItem
from allmychanges.utils import (
    update_fields)
from tqdm import tqdm


def migrate(user):
    if user.send_digest == 'daily':
        before = datetime.datetime(2016, 3, 5)
    elif user.send_digest == 'weekly':
        before = datetime.datetime(2016, 2, 29)
    else:
        return

    items_to_ignore = list(FeedItem.objects.filter(
        user=user,
        created_at__lt=before).order_by('-id'))

    if items_to_ignore and not user.feed_sent_id:
        update_fields(user,
                      feed_sent_id=items_to_ignore[0].id)


class Command(LogMixin, BaseCommand):
    help = u"""Разовая миграция для переезда на send digests 2."""

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in tqdm(users):
            migrate(user)
