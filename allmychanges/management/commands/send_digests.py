# coding: utf-8
import datetime
import os

from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from allmychanges.views import get_digest_for
from premailer import Premailer


class Command(BaseCommand):
    help = u"""Prepares and sends digests to all users."""

    def handle(self, *args, **options):
        now = timezone.now()
        day_ago = now - datetime.timedelta(1)
        week_ago = now - datetime.timedelta(7)
        
        for user in get_user_model().objects.filter(is_active=True):
            today_changes = get_digest_for(user, after_date=day_ago)
            
            if today_changes:
                print 'Sending digest to', user.username, user.email
            
                week_changes = get_digest_for(user,
                                              before_date=day_ago,
                                              after_date=week_ago)         
                body = render_to_string(
                    'emails/digest.html',
                    dict(today_changes=today_changes,
                         week_changes_count=len(week_changes)))

                external_styles = [
                    os.path.join(settings.STATIC_ROOT,
                                 'allmychanges/css',
                                 name)
                    for name in ('reset.css', 'allmychanges.css')]
                premailer = Premailer(body,
                                      base_url='http://art.dev.allmychanges.com:8000/',
                                      external_styles=external_styles)
                body = premailer.transform()
                message = EmailMultiAlternatives('Changelogs digest on {0:%d %B %Y}'.format(now),
                          None,
                          'AllMyChanges.com <noreply@allmychanges.com>',
                          [user.email])
                message.attach_alternative(body.encode('utf-8'), 'text/html')
                message.send()
