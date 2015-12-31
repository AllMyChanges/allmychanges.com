# coding: utf-8

import time

from twiggy_goodies.threading import log


def get_modules():
    from allmychanges.downloaders.vcs import git
    from allmychanges.downloaders.vcs import hg
    from allmychanges.downloaders.vcs import git_commits
    from allmychanges.downloaders import (
        fake,
        github_releases,
        feed,
        appstore,
        google_play,
        http)

    return [
        fake,
        git,
        github_releases,
        git_commits,
        hg,
        http,
        feed,
        appstore,
        google_play,
    ]


def get_downloader_name(module):
    return module.__name__.replace('allmychanges.downloaders.', '')


def get_modules_map():
    return {
        get_downloader_name(module): module
        for module in get_modules()
    }


def guess_downloaders(source):
    # this dict is passed around, to allow
    # downloaders to use information from other downloaders
    # this way, we can disable http downloader, if feed
    # downloader was discovered before

    # TODO: сделать настройку через переменную окружения
    with log.name_and_fields('guesser', source=source):
        log.debug('Guessing downloaders')

        discovered = {}

        modules = get_modules()

        # if True:
        #     yield {'name': 'http'}
        #     yield {'name': 'vcs.git'}
        #     return

        for module in modules:
            name = get_downloader_name(module)
            # print ''
            with log.fields(downloader=name):
                log.debug('Guessing if this downloader can be used')
                start = time.time()

                try:
                    result = module.guess(source, discovered=discovered)
                    end = time.time()
                    with log.fields(elapsed_time=end - start, result=result):
                        log.debug('Guess results')

                    if result:
                        result['name'] = name
                        yield result

                        # this way we could stop if google play or appstore
                        # url was discovered
                        if 'stop' in result:
                            log.debug('Stopping because "stop" key was encountered')
                            break
                        discovered[name] = result
                except RuntimeError:
                    log.trace().error('Ignored error')
                    pass


def get_downloader(name):
    return get_modules_map().get(name).download
