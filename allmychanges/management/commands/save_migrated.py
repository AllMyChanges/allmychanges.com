# coding: utf-8

import os
import shutil
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from twiggy_goodies.threading import log
from twiggy_goodies.django import LogMixin
from allmychanges.downloaders import guess_downloaders
from allmychanges.models import (
    Changelog)
from allmychanges.utils import (
    update_fields)
from clint.textui import progress



DOWNLOADERS_MAP = {
    u'feed': 'feed',
    u'git': 'vcs.git',
    u'github_releases': 'github_releases',
    u'git_commits': 'vcs.git_commits',
    u'hg': 'vcs.hg',
    u'http': 'http',
    u'rechttp': 'http',
    u'google_play': 'google_play',
    u'itunes': 'appstore',
}

def parse_package_name(name):
    try:
        return {'pk': int(name)}
    except ValueError:
        pass

    if '/' in name:
        namespace, name = name.split('/', 1)
        return dict(namespace=namespace,
                    name=name)
    return dict(name=name)


def cleanup_source(source):
    return source.split('+', 1)[-1]


def migrate_settings(downloader, ch):
    downloader_settings = {}
    prev_downloader = ch.downloader

    import re
    is_http = re.compile(ur'^https?://.*')

    search_list = ch.search_list.split('\n')
    ignore_list = ch.ignore_list.split('\n')

    if downloader is 'http':
        downloader_search_list = filter(
            is_http.match, search_list)

        if downloader_search_list:
            downloader_settings['search_list'] = downloader_search_list

        downloader_ignore_list = filter(
            is_http.match, ignore_list)

        if downloader_ignore_list:
            downloader_settings['ignore_list'] = downloader_ignore_list

        if prev_downloader == 'rechttp':
            downloader_settings['recursive'] = True


    search_list = filter(
        lambda line: not is_http.match(line), search_list)
    search_list = u'\n'.join(search_list)

    ignore_list = filter(
        lambda line: not is_http.match(line), ignore_list)
    ignore_list = u'\n'.join(ignore_list)


    return (downloader_settings,
            search_list,
            ignore_list,
            ch.xslt)


def migrate(ch):
    with log.name_and_fields('migrator',
                             changelog=u'{0.namespace}/{0.name}'.format(ch)):

        cache_dir = os.path.join(settings.TEMP_DIR, 'git-cache')
        if os.path.exists(cache_dir):
            log.info('Removing cache_dir')
            shutil.rmtree(cache_dir)

        if not ch.name:
            log.info('Has no name')
            return 'has no name'

        if not ch.downloaders:
            log.info('Migrating')

            downloaders = list(guess_downloaders(ch.source))
            downloader = DOWNLOADERS_MAP.get(ch.downloader)

            if downloader and downloaders:
                downloader_names = set(d['name'] for d in downloaders)

                if downloader not in downloader_names:
                    log.info('Downloader "{0}" is not in the list "{1}"'.format(
                                 downloader,
                                 ', '.join(downloader_names)))
                    log.info('Done 1')
                    return 'downloader not in guessed'

                if downloader == 'git':
                    versions_sources = set(
                        v.source.lower()
                        for v in ch.versions.all())

                    if 'vcs' in versions_sources:
                        downloader = 'vcs.git_commits'

                source = cleanup_source(ch.source)

                (downloader_settings,
                 search_list,
                 ignore_list,
                 xslt) = migrate_settings(downloader, ch)

                try:
                    update_fields(ch,
                                  source=source,
                                  downloaders=downloaders,
                                  downloader=downloader,
                                  downloader_settings=downloader_settings,
                                  search_list=search_list,
                                  ignore_list=ignore_list)
                except Exception as e:
                    if 'Duplicate entry' in str(e):
                        log.trace().error('Duplicate error')
                        return 'duplicate error'
                    raise

                log.info('Downloader is "{0}"'.format(downloader))
            else:
                log.info(('No downloader or downloaders '
                          'and original downloader is "{0}"').format(
                              ch.downloader))
        else:
            log.info('Seems that changelog already migrated')
            return 'already was migrated'

        log.info('Done 2')
        return 'migrated'


class Command(LogMixin, BaseCommand):
    help = u"""Download package sources into a temporary directory."""

    def handle(self, *args, **options):
        filename = 'migration.json'

        data = []
        changelogs = Changelog.objects.all()

        for ch in progress.bar(changelogs):
            if ch.downloaders:
                data.append(
                    dict(
                        pk=ch.pk,
                        name=ch.name,
                        namespace=ch.namespace,
                        source=ch.source,
                        downloaders=ch.downloaders,
                        downloader=ch.downloader,
                        downloader_settings=ch.downloader_settings,
                        search_list=ch.search_list,
                        ignore_list=ch.ignore_list))

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
