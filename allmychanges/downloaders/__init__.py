# coding: utf-8

from twiggy_goodies.threading import log

def get_modules():
    from allmychanges.downloaders.vcs import git
    from allmychanges.downloaders.vcs import hg
    from allmychanges.downloaders import (
        fake,
        github_releases,
        feed,
        appstore,
        google_play,
        http)

    return [
        fake,
        appstore,
        google_play,
        git,
        github_releases,
        hg,
        feed,
        http,
    ]

def get_modules_map():
    return dict(
        (module.__name__.rsplit('.', 1)[-1], module)
        for module in get_modules())


def guess_downloaders(source):
    # this dict is passed around, to allow
    # downloaders to use information from other downloaders
    # this way, we can disable http downloader, if feed
    # downloader was discovered before

    # TODO: сделать настройку через переменную окружения
    print 'Guessing downloaders'

    if False:
        yield {'name': 'hg'}
        yield {'name': 'http'}
        return
    discovered = {}

    modules = get_modules()

    for module in modules:
        result = module.guess(source, discovered=discovered)
        if result:
            name = module.__name__.rsplit('.', 1)[-1]
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
