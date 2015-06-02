import arrow
import requests
import anyjson

from django.core.management.base import BaseCommand
from django.conf import settings
from twiggy_goodies.django import LogMixin
from allmychanges.models import (
    User, MandrillMessage,
    UserHistoryLog)


class Command(LogMixin, BaseCommand):
    help = u"""Sync all users data with our CRM system."""

    def handle(self, *args, **options):
        data = dict(key=settings.MANDRILL_KEY,
                    limit=1000,
                    tags=['allmychanges'])
        response = requests.post(
            'https://mandrillapp.com/api/1.0/messages/search.json',
            data=anyjson.serialize(data),
            headers={'User-Agent': 'AllMyChanges.com Bot',
                     'Content-Type': 'application/json'})

        if response.status_code == 200:
            items = response.json()

            for item in items:
                mid = item['_id']
                print 'Processing', mid
                try:
                    message = MandrillMessage.objects.get(mid=mid)
                    print 'New message created in db'
                    message.payload = anyjson.serialize(item)
                    message.save(update_fields=('payload',))
                except MandrillMessage.DoesNotExist:
                    email = item['email']
                    try:
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        user = None

                    ts = item['ts']
                    created_at = arrow.get(ts)
                    message = MandrillMessage.objects.create(
                        mid=mid,
                        email=email,
                        user=user,
                        timestamp=ts,
                        payload=anyjson.serialize(item))

                    if 'digest' in item['tags']:
                        print 'This is a digest'
                        for click in item['clicks_detail']:
                            print 'Creating a click event'
                            UserHistoryLog.write(
                                user,
                                '',
                                'email-digest-click',
                                'User clicked a link "{0}" in digest email'.format(click['url']),
                                created_at=created_at)
                        for open_detail in item['opens_detail']:
                            print 'Creating a open event'
                            UserHistoryLog.write(
                                user,
                                '',
                                'email-digest-open',
                                'User opened digest email',
                                created_at=created_at)
                    else:
                        print 'Found item {0} with tags "{1}"'.format(
                            mid, item['tags'])
