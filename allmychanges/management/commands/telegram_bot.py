# coding: utf-8
import re
import os.path
import requests
import time
import datetime
import anyjson

from html2text import html2text
from allmychanges.utils import first_sentences
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog
from django.conf import settings
from twiggy_goodies.threading import log
from itertools import izip_longest

# TODO:
# + обрабатывать /start
# - запоминать чаты, чтобы иметь возможность постить туда новости.

def find_changelog(query):
    if '/' in query:
        namespace, name = query.split('/', 1)
    elif ' ' in query:
        namespace, name = query.split(' ', 1)
    else:
        namespace = ''
        name = query

    namespace = namespace.strip()
    name = name.strip()

    def by_namespace(queryset, fuzzy=False, query=None):
        query = query or namespace
        if query:
            if fuzzy:
                return queryset.filter(namespace__istartswith=query)
            else:
                return queryset.filter(namespace=query)
        return queryset

    def by_name(queryset, fuzzy=False):
        if name:
            if fuzzy:
                return queryset.filter(name__istartswith=name)
            else:
                return queryset.filter(name=name)
        return queryset

    active = Changelog.objects.only_active()

    querysets = [by_name(by_namespace(active)),
                 by_name(by_namespace(active), fuzzy=True),
                 by_name(by_namespace(active, fuzzy=True), fuzzy=True),
                 by_namespace(active, fuzzy=True, query=query)]
    for queryset in querysets:
        changelogs = list(queryset)
        if changelogs:
            return changelogs

    return []


def get(method, **params):
    log.info(u'{0} GET {1}'.format(datetime.datetime.now(), method))
    return requests.get(settings.TELEGRAM_BOT_BASE_URL + method, data=params).json()

def post(method, **params):
    log.info(u'{0} POST {1}'.format(datetime.datetime.now(), method))
    return requests.post(settings.TELEGRAM_BOT_BASE_URL + method, data=params).json()


def start_handler(message, query):
    post('sendMessage',
         chat_id=message['chat']['id'],
         text='Hello, master!\n\nI\'m able to help you know what is the latest version of some software library and also will provide a changelog\'s snippet.\n\nJust type a library name. Try, for example, "django" or "ruby".',
         reply_markup=anyjson.serialize(
             dict(hide_keyboard=True)))


def default_handler(message, query):
    changelogs = find_changelog(query)

    def post_no_such_changelog():
        post('sendMessage',
             chat_id=message['chat']['id'],
             text='No such changelog at https://allmychanges.com. Be the first who will add it!',
             reply_markup=anyjson.serialize(
                 dict(hide_keyboard=True)))

    if changelogs:
        if len(changelogs) == 1:
            ch = changelogs[0]
            version = ch.latest_version()
            if version:
                limit = 2000
                no_html = html2text(version.processed_text)
                if len(no_html) > limit:
                    snippet = no_html[:limit] + u'\n...'
                else:
                    snippet = no_html

                post('sendMessage',
                     chat_id=message['chat']['id'],
                     text=(u'{namespace}/{name}, latest version is '
                           u'{version}:\n\n{snippet}\n\nMore information is available '
                           u'at https://allmychanges.com{uri}').format(
                               namespace=ch.namespace,
                               name=ch.name,
                               version=version.number,
                               uri=ch.get_absolute_url(),
                               snippet=snippet),
                     reply_markup=anyjson.serialize(
                         dict(hide_keyboard=True)))
            else:
                post_no_such_changelog()

        else:
            packages = map('{0.namespace}/{0.name}'.format, changelogs)
            packages = iter(packages)
            packages = izip_longest(packages, packages, packages)
            packages = [filter(None, line) for line in packages]

            post('sendMessage',
                 chat_id=message['chat']['id'],
                 text='More than one package looks like this. Please, select one.',
                 reply_markup=anyjson.serialize(
                     dict(keyboard=packages)))
    else:
        post_no_such_changelog()


HANDLERS = [(ur'^/start(@.*)?', start_handler),
            (ur'^.*$', default_handler)]
HANDLERS = [(re.compile(pattern), handler)
            for pattern, handler in HANDLERS]


class Command(LogMixin, BaseCommand):
    help = u"""Send release beats to graphite."""

    def handle(self, *args, **options):
        max_update_id = 0
        while True:
            response = get('getUpdates', timeout=10, offset=max_update_id + 1)
            messages = response['result']
            for message in messages:
                max_update_id = max(max_update_id, message['update_id'])
                message = message['message']
                query = message['text']
                with log.fields(query=query,
                                     from_username=message['chat']['username'],
                                     chat_id=message['chat']['id']):
                    log.info(u'Message received')

                    for matcher, handler in HANDLERS:
                        if matcher.match(query) is not None:
                            handler(message, query)
                            break
