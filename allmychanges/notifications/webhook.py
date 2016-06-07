# coding: utf-8

import requests
import anyjson

from django.conf import settings


def format_tag(tag):
    return dict(
        name=tag.name,
        version=tag.version_number,
    )


def notify_about_version(
        user,
        url,
        version,
        changelog=None):

    def format_date(dt):
        if dt is not None:
            return dt.isoformat()

    if not changelog:
        changelog = version.changelog

    user_tags = list(user.tags.filter(changelog=changelog))

    webhook_data = dict(
        namespace=changelog.namespace,
        name=changelog.name,
        version=dict(number=version.number,
                       web_url=settings.BASE_URL + version.get_absolute_url(),
                       content=version.processed_text,
                       released_at=format_date(version.date),
                       discovered_at=format_date(version.discovered_at)),
        user_tags=map(format_tag, user_tags))

    webhook_data = anyjson.serialize(webhook_data)
    requests.post(url,
                  data=webhook_data,
                  headers={'User-Agent': settings.HTTP_USER_AGENT,
                           'Content-Type': 'application/json'})
