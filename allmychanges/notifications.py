import os

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from premailer import Premailer


def send_email(recipient, subject, template, context={}, tags=[]):
    body = render_to_string('emails/' + template,
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

    headers = {}
    if tags:
        # add special header to tag messages in Mandrill
        # http://help.mandrill.com/entries/21688056-Using-SMTP-Headers-to-customize-your-messages#tag-your-messages
        headers['X-MC-Tags'] = ','.join(tags)

    message = EmailMultiAlternatives(
        subject,
        None,
        'AllMyChanges.com <noreply@allmychanges.com>',
        [recipient],
        headers=headers)
    message.attach_alternative(body.encode('utf-8'), 'text/html')
    message.send()
