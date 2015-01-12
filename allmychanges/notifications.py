from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email(recipient, subject, template, context):
    body = render_to_string('emails/' + template,
                            context)
    message = EmailMultiAlternatives(subject,
                                     None,
                                     'AllMyChanges.com <noreply@allmychanges.com>',
                                     [recipient])
    message.attach_alternative(body.encode('utf-8'), 'text/html')
    message.send()
