# coding: utf-8

import re
import requests
import anyjson

from django.conf import settings

from allmychanges.utils import html2md


# These functions convert from markdown to
# Slack's markup format:
# https://api.slack.com/docs/formatting

def convert_md_links(text):
    return re.sub(
        ur'\[(?P<text>.*?)\]\((?P<link>\S+?)\)',
        u'<\g<link>|\g<text>>',
        text)


def convert_md_bolds(text):
    return re.sub(
        ur'\*\*(?P<text>\S.*?\S)\*\*',
        u'*\g<text>*',
        text)


def convert_md_images(text):
    return re.sub(
        ur'!\[(?P<text>\S.*?\S)?\]\((?P<link>\S+?)\)',
        u'\g<link>',
        text)


def format_tag_for_slack(tag):
    return '<{0}|{1} ({2})>'.format(
        settings.BASE_URL + tag.get_absolute_url(),
        tag.name,
        tag.version_number)


def notify_about_version(
        user,
        url,
        version,
        changelog=None,
        subject=u'New Version Released'):
    markdown_text = html2md(version.processed_text)

    text = re.sub(ur'^  \* ', ur'- ', markdown_text, flags=re.MULTILINE)
    text = re.sub(ur'^## (.*)', ur'*\1*', text, flags=re.MULTILINE)
    text = re.sub(ur'^#{3,5} (.*)', ur'_\1_', text, flags=re.MULTILINE)
    text = convert_md_links(text)
    text = convert_md_images(text)
    text = convert_md_bolds(text)

    if not changelog:
        changelog = version.changelog

    version_url = settings.BASE_URL + version.get_absolute_url()
    project_url = settings.BASE_URL + changelog.get_absolute_url()
    user_tags = list(user.tags.filter(changelog=changelog))
    if user_tags:
        formatted_tags = u', '.join(map(format_tag_for_slack, user_tags))
    else:
        formatted_tags = u'<{0}|add some tags!>'.format(
            project_url + '?add-tags')

# These comments are for debug
# and can be removed when I decide what to do with images
# which aren't displayed in attachments

 #    text = """

 # http://placehold.it/300x250

 # """ + text

#     text = """*Usual* text with image:

# http://placehold.it/300x210

# Next line"""
    # send(url, text)
    # return
    send_as_attachment(
        url,
        subject,
        text,
        fallback=u'Version {v} of {namespace}/{name} was released.'.format(
            v=version.number,
            namespace=changelog.namespace,
            name=changelog.name),
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
            dict(title='Tags',
                 value=formatted_tags,
                 short=True),
        ]
    )


def send(url, text):
    data = {
        'text': text,
        'username': 'AllMyChanges.com',
    }

    requests.post(url, data=anyjson.serialize(data))


def send_as_attachment(url, subject, text, fields=[], fallback=''):
    # https://api.slack.com/docs/formatting/builder?msg=%7B%22attachments%22%3A%5B%7B%22text%22%3A%22Some%20*text*%20in%20%3Chttp%3A%2F%2Fexample.com%7CMarkdown%3E%22%7D%5D%2C%22username%22%3A%22AllMyChanges.com%22%7D
    data = {
        'attachments': [
            {
                'pretext': subject,
                'fields': fields,
                'fallback': fallback,
                'mrkdwn_in': ['pretext', 'fields'],
            },
            {
                'pretext': 'Release Notes:',
                'text': text,
                'mrkdwn_in': ['text'],
            }
        ],
        'username': 'AllMyChanges.com',
    }

    requests.post(url, data=anyjson.serialize(data))
