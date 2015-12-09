# coding: utf-8

import time

#from twiggy_goodies.threading import log


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
    print 'Guessing downloaders'

    discovered = {}

    modules = get_modules()

    if True:
        yield {'name': 'http'}
        yield {'name': 'vcs.git'}
        return

    for module in modules:
        name = get_downloader_name(module)
        print ''
        print 'Guessing if {0} can be used'.format(name)
        start = time.time()

        result = module.guess(source, discovered=discovered)
        end = time.time()
        print 'Guess took {0} seconds'.format(end - start)
        print 'Result is:', result

        if result:
            result['name'] = name
            print result
            yield result

            # this way we could stop if google play or appstore
            # url was discovered
            if 'stop' in result:
                break
            discovered[name] = result


def get_downloader(name):
    return get_modules_map().get(name).download
