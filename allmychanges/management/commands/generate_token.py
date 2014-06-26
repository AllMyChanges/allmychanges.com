import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from twiggy_goodies.django import LogMixin

from allmychanges.models import User
from oauth2_provider.models import AccessToken, Application


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        for username in args:
            user = User.objects.get(username=username)
            access_token = AccessToken(
                user=user,
                scope='read write',
                expires=timezone.now() + datetime.timedelta(0, settings.ACCESS_TOKEN_EXPIRE_SECONDS),
                token='boo',
                application=Application.objects.get(pk=1))
            access_token.save()
