# coding: utf-8

import requests
import os
import shutil
import tempfile

from hashlib import md5
from collections import defaultdict
from django.conf import settings
from twiggy_goodies.threading import log
from allmychanges.downloaders.utils import normalize_url
from allmychanges.utils import (
    cd,
    do,
    first_sentences)


def split_branch(url):
    if '@' in url:
        return url.split('@', 1)
    return url, None


def get_github_api_url(username, repo, handle):
    if username and repo:
        return "https://api.github.com/repos/{username}/{repo}/{handle}".format(
            handle=handle, username=username,  repo=repo)


def get_github_auth_headers():
    return {'Authorization': 'token ' + settings.GITHUB_TOKEN}


def download(*args, **params):
    with log.name_and_fields('vcs.git'):
        return _download(*args, **params)


def _download(source, **params):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url, username, repo_name = normalize_url(source)
    cache_dir = os.path.join(settings.TEMP_DIR,
                             'git-cache',
                             md5(url).hexdigest())

    with log.fields(url=url,
                    username=username,
                    repo=repo_name,
                    cache_dir=cache_dir):
        url, branch = split_branch(url)

        with cd(path):
            if not os.path.exists(cache_dir):
                log.info('Cloning into cache dir')

                response = do(
                    'git clone --quiet --bare {url} {path}'.format(
                        url=url,
                        path=cache_dir),
                    timeout=5 * 60)

                if response.status_code != 0:
                    if os.path.exists(cache_dir):
                        shutil.rmtree(cache_dir)
                    raise RuntimeError('Bad status_code from git clone: {0}. '
                                       'Git\'s stderr: {1}'.format(
                                           response.status_code, response.std_err))
            else:
                if settings.ENVIRONMENT == 'unittest':
                    log.info('Skipping git fetch for this project because we are in unittest environment')
                else:
                    response = do(
                        'bash -c \'cd {path} && git fetch\''.format(
                            path=cache_dir),
                        timeout=5 * 60,
                        shell=True)
                    if response.status_code != 0:
                        if os.path.exists(cache_dir):
                            shutil.rmtree(cache_dir)
                        raise RuntimeError('Bad status_code from git clone: {0}. '
                                           'Git\'s stderr: {1}'.format(
                                               response.status_code, response.std_err))


            log.info('Cloning from cache dir')
            response = do('git clone --quiet {url} {path}'.format(
                url=cache_dir,
                path=path))
            if response.status_code != 0:
                if os.path.exists(path):
                    shutil.rmtree(path)
                raise RuntimeError('Bad status_code from git clone: {0}. '
                                   'Git\'s stderr: {1}'.format(
                                       response.status_code, response.std_err))

            if branch:
                with log.fields(branch=branch):
                    log.info('Switching to branch')

                    response = do(
                        'git checkout -b {branch} origin/{branch}'.format(
                            branch=branch))

                    if response.status_code != 0:
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        raise RuntimeError('Bad status_code from git checkout -b {0}: {1}. '
                                           'Git\'s stderr: {2}'.format(
                                               branch, response.status_code, response.std_err))

            log.info('Done')

    return path


def guess(*args, **kwargs):
    with log.name_and_fields('vcs.git'):
        return _guess(*args, **kwargs)


def _guess(source, discovered={}, callback=None):
    """Тут callback используется для того, чтобы сделать
    дополнительные проверки скачанного репозитория.
    Ему передается path и словарь result.
    Callback может вернуть словарь, и тот будет использован
    вместо result. Если callback вернул None,
    то считается что guess прошел безуспешно.
    """

    result = defaultdict(dict)
    source, username, repo = normalize_url(source)

    path = ''
    try:
        path = _download(source)
        # if everything is OK, start populating result
        result['changelog']['source'] = source

        if 'github.com' in source and username and repo:
            result['params'].update(dict(username=username, repo=repo))

            try:
                extended = get_github_name_and_description(username, repo) or {}
                result['changelog'].update(extended)
            except Exception:
                log.trace().error('Ignoring error')
                pass

        if callable(callback):
            return callback(path, result)
        else:
            return result

    except RuntimeError:
        # ignore errors because most probably, they are from git command
        # which won't be able to clone repository from strange url
        log.trace().error('Unable to guess')

    finally:
        if os.path.exists(path):
            shutil.rmtree(path)


def get_github_name_and_description(username, repo):
    from allmychanges.models import DESCRIPTION_LENGTH
    api_url = get_github_api_url(username, repo, '')

    if api_url:
        response = requests.get(api_url.rstrip('/'),
                                headers=get_github_auth_headers())
        data = response.json()
        try:
            name = data['name']
            namespace = data['language']
            if namespace:
                namespace = namespace.lower()
            description = data['description']
            if description:
                description = first_sentences(description,
                                              DESCRIPTION_LENGTH)
        except KeyError:
            log.trace().error('Ignoring KeyError')
            pass

    return dict(namespace=namespace,
                name=name,
                description=description)
