# coding: utf-8

import re
import requests
import anyjson
import html2text
from django.conf import settings


def notify_about_version(url, version, subject=u'New version released'):
    text = html2text.html2text(version.processed_text)
    text = re.sub(ur'^## (.*)', ur'*\1*', text, flags=re.MULTILINE)
    text = re.sub(ur'^#{3,5} (.*)', ur'_\1_', text, flags=re.MULTILINE)

    ch = version.changelog
    version_url = settings.BASE_URL + version.get_absolute_url()
    print 'NOTIFY:', version_url
    text = u"""*{subject} – {namespace}/{name} <{url}|{number}>*

{text}""".format(
    url=version_url,
    subject=subject,
    namespace=ch.namespace,
    name=ch.name,
    number=version.number,
    text=text)

    send(url, text)


def send(url, text):
    data = {'text': text,
            'username': 'AllMyChanges.com',
            'mrkdwn': True,
    }

    requests.post(url, data=anyjson.serialize(data))
