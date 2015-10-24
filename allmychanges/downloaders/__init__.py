# coding: utf-8

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
        appstore,
        google_play,
        git,
        github_releases,
        git_commits,
        hg,
        feed,
        http,
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
        yield {'name': 'vcs.git_commits'}
        return

    for module in modules:
        result = module.guess(source, discovered=discovered)
        if result:
            name = get_downloader_name(module)
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
