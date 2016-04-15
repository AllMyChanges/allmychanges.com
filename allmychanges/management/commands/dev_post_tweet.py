# coding: utf-8
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


class Command(LogMixin, BaseCommand):
    help = u"""Posts tweets about versions."""

    def handle(self, *args, **options):
        v = None

        if args:
            namespace, name = args
            ch = Changelog.objects.get(namespace=namespace,
                                       name=name)
            v = ch.latest_version()
        else:
            for ch in Changelog.objects.good():
                v = ch.latest_version()
                if v is not None and not v.tweet_id:
                    break

        if v is not None:
            v.post_tweet()
            print 'Posted tweet for {0}/{1}'.format(
                ch.namespace, ch.name)
