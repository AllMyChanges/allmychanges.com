# coding: utf-8
import datetime
import os
import times
import logging

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from allmychanges.views import get_digest_for
from allmychanges.utils import dt_in_window
from premailer import Premailer


def send_digest_to(user, code_version='v1'):
    now = timezone.now()
    day_ago = now - datetime.timedelta(1)
    week_ago = now - datetime.timedelta(7)

    today_changes = get_digest_for(user.packages,
                                   after_date=day_ago,
                                   code_version=code_version)

    if today_changes:
        print 'Sending {0} digest to {1} {2}'.format(code_version, user.username, user.email)
        for package in today_changes:
            print '\t{namespace}/{name}'.format(**package)
            for version in package['versions']:
                print '\t\tversion={number}, date={date}, discovered_at={discovered_at}'.format(
                    **version)

        week_changes = get_digest_for(user.packages,
                                      before_date=day_ago,
                                      after_date=week_ago,
                                      code_version=code_version)
        body = render_to_string(
            'emails/digest.html',
            dict(current_user=user,
                 today_changes=today_changes,
                 week_changes_count=len(week_changes)))

        external_styles = [
            os.path.join(settings.STATIC_ROOT,
                         'allmychanges/css',
                         name)
            for name in ('email.css',)]
        premailer = Premailer(body,
                              base_url='http://allmychanges.com/',
                              external_styles=external_styles,
                              disable_validation=True)

        body = premailer.transform()
        subject = 'Changelogs digest on {0:%d %B %Y}'.format(now)
        if code_version == 'v2':
            subject += ' (v2)'

        if code_version == 'v2' and user.username != 'svetlyak40wt':
            email = 'svetlyak.40wt+v2@gmail.com'
        else:
            email = user.email

        message = EmailMultiAlternatives(subject,
                  None,
                  'AllMyChanges.com <noreply@allmychanges.com>',
                  [email])

        if user.username != 'svetlyak40wt':
            message.bcc.append('svetlyak.40wt+changes@gmail.com')

        message.attach_alternative(body.encode('utf-8'), 'text/html')
        message.send()


class Command(LogMixin, BaseCommand):
    help = u"""Prepares and sends digests to all users."""

    def handle(self, *args, **options):
        # this will disable cssutil's logger
        cssutils_logger = logging.getLogger('CSSUTILS')
        cssutils_logger.level = logging.ERROR

        now = timezone.now()
        utc_now = times.to_universal(now)
        all_timezones = get_user_model().objects.all().values_list(
            'timezone', flat=True).distinct()
        send_for_timezones = [tz for tz in all_timezones
                              if tz and dt_in_window(tz, utc_now, 9)]
        
        users = get_user_model().objects.exclude(email='')
        
        if args:
            users = users.filter(username__in=args)
        else:
            users = users.filter(timezone__in=send_for_timezones)
        
        for user in users:
            send_digest_to(user, code_version='v1')
            send_digest_to(user, code_version='v2')
