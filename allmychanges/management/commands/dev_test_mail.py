# coding: utf-8
import os
import logging

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from premailer import Premailer

from allmychanges.notifications.email import send_email


def send_email_using_template(address, subject, template, **context):
    if not isinstance(address, (list, tuple)):
        address = (address,)

    body = render_to_string(
        'emails/{0}.html'.format(template),
        context)

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
    message = EmailMultiAlternatives(
        subject,
        None,
        'AllMyChanges.com <noreply@allmychanges.com>',
        address)

    message.attach_alternative(body.encode('utf-8'), 'text/html')
    message.send()


class Command(LogMixin, BaseCommand):
    help = u"""Prepares and sends digests to all users."""

    def handle(self, *args, **options):
        # this will disable cssutil's logger
        to_email, template = args

        cssutils_logger = logging.getLogger('CSSUTILS')
        cssutils_logger.level = logging.ERROR

        send_email(
            to_email,
            u'Тестовый email',
            template + '.html',
            tags=('allmychanges', 'test'))
