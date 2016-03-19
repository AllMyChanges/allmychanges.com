# coding: utf-8

import re
import requests
import anyjson
import html2text
from django.conf import settings

from allmychanges.utils import first_sentences


# These functions convert from markdown to
# Slack's markup format:
# https://api.slack.com/docs/formatting

def convert_md_links(text):
    return re.sub(
        ur'\[(?P<text>\S.*?\S)\]\((?P<link>\S+?)\)',
        u'<\g<link>|\g<text>>',
        text)


def convert_md_bolds(text):
    return re.sub(
        ur'\*\*(?P<text>\S.*?\S)\*\*',
        u'*\g<text>*',
        text)


def notify_about_version(url,
                         version,
                         changelog=None,
                         subject=u'New Version Released'):
    markdown_text = html2text.html2text(version.processed_text)

    text = re.sub(ur'^  \* ', ur'- ', markdown_text, flags=re.MULTILINE)
    text = re.sub(ur'^## (.*)', ur'*\1*', text, flags=re.MULTILINE)
    text = re.sub(ur'^#{3,5} (.*)', ur'_\1_', text, flags=re.MULTILINE)
    text = convert_md_links(text)
    text = convert_md_bolds(text)

    if not changelog:
        changelog = version.changelog

    version_url = settings.BASE_URL + version.get_absolute_url()
    project_url = settings.BASE_URL + changelog.get_absolute_url()

    send_as_attachment(
        url,
        subject,
        text,
        fields=[
            dict(title='Project',
                 value=u'<{0}|{1}/{2}>'.format(
                     project_url,
                     changelog.namespace,
                     changelog.name,
                 ),
                 short=True),
            dict(title='Version',
                 value=u'<{0}|{1}>'.format(version_url, version.number),
                 short=True),
        ]
    )


def send(url, text):
    data = {
        'text': text,
        'username': 'AllMyChanges.com',
    }

    requests.post(url, data=anyjson.serialize(data))


def send_as_attachment(url, subject, text, fields=[]):
    # https://api.slack.com/docs/formatting/builder?msg=%7B%22attachments%22%3A%5B%7B%22text%22%3A%22Some%20*text*%20in%20%3Chttp%3A%2F%2Fexample.com%7CMarkdown%3E%22%7D%5D%2C%22username%22%3A%22AllMyChanges.com%22%7D
    data = {
        'attachments': [
            {
                'pretext': subject,
                'fields': fields,
                'mrkdwn_in': ['pretext', 'fields'],
            },
            {
                'pretext': 'Release Notes:',
                'fallback': first_sentences(text, 1000),
                'text': text,
                'mrkdwn_in': ['text'],
            }
        ],
        'username': 'AllMyChanges.com',
    }

    requests.post(url, data=anyjson.serialize(data))
