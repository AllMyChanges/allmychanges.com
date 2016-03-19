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
                         subject=u'New version released'):
    text = html2text.html2text(version.processed_text)

    text = re.sub(ur'^  \* ', ur'- ', text, flags=re.MULTILINE)
    text = re.sub(ur'^## (.*)', ur'*\1*', text, flags=re.MULTILINE)
    text = re.sub(ur'^#{3,5} (.*)', ur'_\1_', text, flags=re.MULTILINE)
    text = convert_md_links(text)
    text = convert_md_bolds(text)

    if not changelog:
        changelog = version.changelog

    version_url = settings.BASE_URL + version.get_absolute_url()
    text = u"""*{subject} – {namespace}/{name} <{url}|{number}>*

{text}""".format(
    url=version_url,
    subject=subject,
    namespace=changelog.namespace,
    name=changelog.name,
    number=version.number,
    text=text)

    send(url, text)


def send(url, text):
    data = {
        'text': text,
        'username': 'AllMyChanges.com',
        'mrkdwn': True,
    }

    requests.post(url, data=anyjson.serialize(data))


def send_attachment(url, text, fields=[]):
    # markup inside attachements does not work as expected
    # only links are supported:
    # https://api.slack.com/docs/formatting/builder?msg=%7B%22attachments%22%3A%5B%7B%22text%22%3A%22Some%20*text*%20in%20%3Chttp%3A%2F%2Fexample.com%7CMarkdown%3E%22%7D%5D%2C%22username%22%3A%22AllMyChanges.com%22%7D
    data = {
        'attachments': [
            {
                'fallback': first_sentences(text, 1000),
                'text': text,
                'fields': fields,
            }
        ],
        'username': 'AllMyChanges.com',
    }

    requests.post(url, data=anyjson.serialize(data))
