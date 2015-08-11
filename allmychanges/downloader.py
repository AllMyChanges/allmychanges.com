# coding: utf-8
import codecs
import urlparse
import anyjson
import tempfile
import re
import os.path
import shutil
import envoy
import requests
import plistlib
import lxml
import feedparser

from cgi import parse_header
from django.conf import settings
from urlparse import urlsplit
from allmychanges.utils import (
    cd, get_text_from_response, is_http_url,
    first_sentences,
    html_document_fromstring)
from allmychanges.exceptions import DownloaderWarning, AppStoreAppNotFound
from allmychanges.markdown import render_markdown
from twiggy_goodies.threading import log


def old_guess_downloader(url):
    parts = urlsplit(url)

    start_map = {'test+': 'fake',
                 'rechttp+': 'rechttp',
                 'git+': 'git',
                 'http+': 'http',
                 'rss+': 'feed',
                 'atom+': 'feed',
                 'feed+': 'feed',
                 'gh-releases+': 'github_releases',
                 'github-releases+': 'github_releases',
                 'github_releases+': 'github_releases'}

    for prefix, downloader in start_map.items():
        if url.startswith(prefix):
            return downloader

    if parts.hostname == 'itunes.apple.com':
        return 'itunes'

    if parts.hostname == 'play.google.com':
        return 'google_play'

    if parts.hostname == 'github.com':
        url, username, repo = normalize_url(url)
        if username and repo:
            # first wi'll check for release
            releases = get_github_releases(username, repo)
            if releases:
                return 'github_releases'

            # then we sure it is a git repo
            # otherwise, we have to try downloaders one after another
            return 'git'

    downloaders = [('git', git_downloader),
                   ('hg', hg_downloader),
                   ('http', http_downloader)]

    for name, downloader in downloaders:
        try:
            path = downloader(url)
            shutil.rmtree(path)
            return name
        except Exception:
            pass

    return None


def old_get_downloader(name):
    return globals().get(name + '_downloader')


def old_get_namespace_guesser(name):
    """Actually it is not only namespace guesser,
    but also a name and description guesser.

    Each guesser should return a dict with name, namespace and description fields.
    """
    null_guesser = lambda url: dict(namespace=None,
                                    name=None,
                                    description=None)
    return globals().get(name + '_guesser', null_guesser)
