# coding: utf-8

import requests
import tempfile
import shutil
import codecs
import os
import re

from collections import defaultdict
from django.conf import settings
from allmychanges.downloaders.utils import normalize_url
from allmychanges.markdown import render_markdown
from allmychanges.downloaders.vcs.git import (
    get_github_api_url,
    get_github_name_and_description,
    get_github_auth_headers)
from allmychanges.utils import cd
from twiggy_goodies.threading import log


def guess(source, discovered={}):
    result = defaultdict(dict)

    if 'github.com' in source:
        try:
            url, username, repo = normalize_url(source)
            releases = get_github_releases(username, repo)
            if releases:
                result['changelog']['source'] = url
                result['params'].update(dict(username=username, repo=repo))
                extended = get_github_name_and_description(username, repo) or {}
                result['changelog'].update(extended)
        except:
            pass

    return result



def download(source, **params):
    url, username, repo = normalize_url(source)
    releases = get_github_releases(username, repo)

    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    with cd(path):
        try:
            with codecs.open(
                    os.path.join(path, 'GitHubReleases.html'),
                    'w',
                    'utf-8') as f:
                if releases:
                    for release in releases:
                        if not release.get('draft'):
                            name = release.get('name', '').lstrip('v')
                            tag = release.get('tag_name', '').lstrip('v')
                            # если тег совпадает с названием, то не надо
                            # добавлять лишнего подзаголовка
                            if name == tag \
                               or re.match(ur'version {0}'.format(tag), name, re.I) \
                               or re.match(ur'{0} release'.format(tag), name, re.I) \
                               or re.match(ur'{repo} v?{tag}'.format(repo=repo, tag=tag), name, re.I):
                                name = None

                            # вот что ответили ребята из github:
                            # The `created_at` timestamp is for the GitHub Release itself.
                            # The `published_at` timestamp represents the time that the Tag
                            # was created. This can be in the past if an annotated tag's date is
                            # in the past, or the tag's commit date is in the past.

                            title = tag.strip()
                            if title:
                                f.write(u'<h1>{0}</h1>\n'.format(title))

                            if name:
                                f.write(u'<h2>{0}</h2>\n'.format(name))

                            date = release.get('created_at')
                            if date:
                                f.write(u'<div style="display: none">{0}</div>\n\n'.format(
                                    date))


                            body = release['body'].replace('\r\n', '\n')
                            html_body = render_markdown(body)
                            html_body = u'<article>\n\n{0}\n\n</article>'.format(html_body)
                            f.write(html_body)
                            f.write('\n\n')
        except:
            shutil.rmtree(path)
            raise
    return path


def get_github_releases(username, repo):
    api_url = get_github_api_url(username, repo, 'releases')
    if api_url:
        with log.name_and_fields('downloader.github', url=api_url):
            response = requests.get(api_url,
                                    headers=get_github_auth_headers())
            status_code = response.status_code

            if status_code == 404:
                return

            if status_code != 200:
                with log.fields(status_code=status_code):
                    log.error('Bad status code from GitHub')
                raise RuntimeError('Bad status code from GitHub')
            data = response.json()
        return data
