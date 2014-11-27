import tempfile
import re
import os.path
import shutil
import envoy
import requests

from django.conf import settings
from urlparse import urlsplit
from .utils import cd


def normalize_url(url, for_checkout=True):
    """Normalize url either for browser or for checkout.
    Usually, difference is in the schema.
    It normalizes url to 'git@github.com:{username}/{repo}' and also
    returns username and repository's name.
    """
    for_browser = not for_checkout
    github_template = 'git://github.com/{username}/{repo}'
    bitbucket_template = 'https://bitbucket.org/{username}/{repo}'

    if for_browser:
        github_template = 'https://github.com/{username}/{repo}'

    url = url.replace('git+', '')

    if 'github' in url:
        regex = r'github.com[/:](?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]+?)(?:\.git$|/$|/tree/master$|$)'
        match = re.search(regex, url)
        if match is None:
            # some url to a raw file or github wiki
            return (url, None, None)
        else:
            username, repo = match.groups()
            return (github_template.format(**locals()),
                    username,
                    repo)


    elif 'bitbucket' in url:
        regex = r'bitbucket.org/(?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]*)'
        username, repo = re.search(regex, url).groups()
        return (bitbucket_template.format(**locals()),
                username,
                repo)

    return (url, None, url.rsplit('/')[-1])



def download_repo(url, pull_if_exists=True):
    url, username, repo = normalize_url(url)

    path = os.path.join(settings.REPO_ROOT, username, repo)

    if os.path.exists(os.path.join(path, '.failed')):
        return None

    if os.path.exists(path):
        if pull_if_exists:
            with cd(path):
                response = envoy.run('git checkout master')
                if response.status_code != 0:
                    raise RuntimeError(
                        'Bad status_code from git checkout master: '
                        '{0}. Git\'s stderr: {1}'.format(
                            response.status_code, response.std_err))

                response = envoy.run('git pull')
                if response.status_code != 0:
                    raise RuntimeError('Bad status_code from git pull: '
                                       '{0}. Git\'s stderr: {1}'.format(
                                           response.status_code,
                                           response.std_err))
    else:
        response = envoy.run('git clone {url} {path}'.format(url=url,
                                                             path=path))

        if response.status_code != 0:
            os.makedirs(path)
            with open(os.path.join(path, '.failed'), 'w') as f:
                f.write('')
            raise RuntimeError('Bad status_code from git clone: {0}. '
                               'Git\'s stderr: {1}'.format(
                                   response.status_code, response.std_err))

    return path


def fake_downloader(source):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)

    source = source.replace('test+', '')

    if os.path.isfile(source):
        shutil.copyfile(
            source,
            os.path.join(path, 'CHANGELOG'))
        return path
    else:
        destination = os.path.join(path, 'project')
        shutil.copytree(source, destination)
        return destination


def split_branch(url):
    if '@' in url:
        return url.split('@', 1)
    return url, None


def git_downloader(source):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url, username, repo_name = normalize_url(source)

    url, branch = split_branch(url)

    with cd(path):
        response = envoy.run('git clone {url} {path}'.format(url=url,
                                                             path=path))
        if response.status_code != 0:
            if os.path.exists(path):
                shutil.rmtree(path)
            raise RuntimeError('Bad status_code from git clone: {0}. '
                               'Git\'s stderr: {1}'.format(
                                   response.status_code, response.std_err))

        if branch:
            response = envoy.run('git checkout -b {branch} origin/{branch}'.format(branch=branch))

            if response.status_code != 0:
                if os.path.exists(path):
                    shutil.rmtree(path)
                raise RuntimeError('Bad status_code from git checkout -b {0}: {1}. '
                                   'Git\'s stderr: {2}'.format(
                                       branch, response.status_code, response.std_err))

    return path

def hg_downloader(source):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = source.replace('hg+', '')

    with cd(path):
        response = envoy.run('hg clone {url} {path}'.format(url=url,
                                                             path=path))
    if response.status_code != 0:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise RuntimeError('Bad status_code from hg clone: {0}. '
                           'Mercurial\'s stderr: {1}'.format(
                               response.status_code, response.std_err))

    return path


def http_downloader(source):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = source.replace('http+', '')

    try:
        with cd(path):
            response = requests.get(url)
            with open('ChangeLog', 'w') as f:
                f.write(response.text.encode('utf-8'))

    except Exception, e:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise RuntimeError('Unexpected exception "{0}" when fetching: {1}'.format(
            e, url))
    return path


def guess_downloader(url):
    parts = urlsplit(url)

    if parts.hostname == 'github.com':
        url, username, repo = normalize_url(url)
        if username and repo:
            # then we sure it is a git repo
            # otherwise, we have to try downloaders one after another
            return 'git'

    if url.startswith('test+'):
        return 'fake'

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


def get_downloader(name):
    return globals().get(name + '_downloader')
