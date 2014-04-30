import os
import re
import string
import envoy
import logging
import graphitesend
import time
import tempfile
import shutil
import times
import requests
    
from lxml import html
from contextlib import contextmanager

from django.contrib.markup.templatetags import markup
from django.conf import settings
from django.utils.encoding import force_text
from django.utils import timezone

from allmychanges.crawler import search_changelog, parse_changelog


MINUTE = 60
HOUR = 60 * MINUTE

def load_data(filename):
    data = []
    with open(filename) as f:
        for line in f.readlines():
            data.append(
                tuple(map(string.strip, line.split(';', 1))))

    return data


@contextmanager
def cd(path):
    """Usage:

    with cd(to_some_dir):
        envoy.run('task do')
    """
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


def get_package_metadata(path, field_name):
    """Generates PKG-INFO and extracts given field.
    Example:
    get_package_metadata('/path/to/repo', 'Name')
    """
    with cd(path):
        response = envoy.run('python setup.py egg_info')
        for line in response.std_out.split('\n'):
            if 'PKG-INFO' in line:
                with open(line.split(None, 1)[1]) as f:
                    text = f.read()
                    match = re.search(r'^{0}: (.*)$'.format(field_name),
                                      text,
                                      re.M)
                    if match is not None:
                        return match.group(1)


def normalize_url(url,
                  github_template='git://github.com/{username}/{repo}',
                  bitbucket_template='https://bitbucket.org/{username}/{repo}'):
    """Normalizes url to 'git@github.com:{username}/{repo}' and also
    returns username and repository's name."""
    url = url.replace('git+', '')
    
    if 'github' in url:
        regex = r'[/:](?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]*)'
        match = re.search(regex, url)
        if match is not None:
            username, repo = match.groups()
            if url.startswith('git@'):
                return url, username, repo
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


def get_markup_type(filename):
    """Return markdown or rest or None"""
    extension = filename.rsplit('.', 1)[-1].lower()
    mapping = dict(
        markdown={'md', 'markdown', 'mdown'},
        rest={'rst', 'rest'},
    )
    for markup_type, possible_extensions in mapping.items():
        if extension in possible_extensions:
            return markup_type


def get_commit_type(commit_message):
    """Return new or fix or None"""
    commit_message = commit_message.lower()
    if commit_message.startswith('add'):
        return 'new'
    elif commit_message.startswith('new '):
        return 'new'
    elif '[new]' in commit_message:
        return 'new'
    elif commit_message.startswith('fix'):
        return 'fix'
    elif ' fixes' in commit_message:
        return 'fix'
    elif ' fixed' in commit_message:
        return 'fix'
    elif 'bugfix' in commit_message:
        return 'fix'
    elif '[fix]' in commit_message:
        return 'fix'
    return 'new'


def get_clean_text_from_html(raw_html):
    if not raw_html:
        return ''
    return html.tostring(html.fromstring(force_text(raw_html)),
                         method='text', encoding=unicode)


def get_clean_text_from_markup_text(text, markup_type):
    raw_html = render_text_for_markup_type(text, markup_type=markup_type)
    return get_clean_text_from_html(raw_html)


def render_text_for_markup_type(text, markup_type):
    if markup_type == 'markdown':
        return render_markdown(text)
    elif markup_type == 'rest':
        return render_rest(text)
    else:
        return text


def render_markdown(text):
    if text is None:
        text = ''
    return markup.markdown(force_text(text))


def render_rest(text):
    if text is None:
        text = ''
    return markup.restructuredtext(force_text(text))


def graphite_send(**kwargs):
    try:
        g = graphitesend.init(prefix=settings.GRAPHITE_PREFIX + '.',
                              graphite_server=settings.GRAPHITE_HOST)
        g.send_dict(kwargs)
    except Exception:
        logging.getLogger('django').exception('Graphite is down')


def count(metric_key, value=1):
    """Log some metrics to process with logster and graphite."""
    logging.getLogger('stats').info(
        'METRIC_COUNT metric={metric} value={value}'.format(
            metric=metric_key, value=value))


@contextmanager
def count_time(metric_key):
    """Log some timings to process with logster and graphite."""
    start = time.time()
    try:
        yield
    finally:
        value = time.time() - start
        logging.getLogger('stats').info(
            'METRIC_TIME metric={metric} value={value}s'.format(
                metric=metric_key, value=value))


def show_debug_toolbar(request):
    return True


def update_changelog_from_raw_data(changelog, raw_data):
    for raw_version in raw_data:
        version, created = changelog.versions.get_or_create(number=raw_version['version'])
        raw_date = raw_version.get('date')
        if raw_date is None:
            if version.date is None:
                version.date = timezone.now()
        else:
            version.date = raw_date
        version.save()

        version.sections.all().delete()
        for raw_section in raw_version['sections']:
            section = version.sections.create(notes=raw_section.get('notes'))
            for raw_item in raw_section.get('items', []):
                section.items.create(text=raw_item, type=get_commit_type(raw_item))


def fake_downloader(changelog):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    shutil.copyfile(
        changelog.source.replace('test+', ''),
        os.path.join(path, 'CHANGELOG'))
    return path

    
def git_downloader(changelog):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url, username, repo_name = normalize_url(changelog.source)

    with cd(path):
        response = envoy.run('git clone {url} {path}'.format(url=url,
                                                             path=path))
    if response.status_code != 0:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise RuntimeError('Bad status_code from git clone: {0}. '
                           'Git\'s stderr: {1}'.format(
                               response.status_code, response.std_err))

    return path


def hg_downloader(changelog):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = changelog.source.replace('hg+', '')

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


def http_downloader(changelog):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = changelog.source.replace('http+', '')
    
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

    
def choose_downloader(changelog):
    source = changelog.source
    
    if source.startswith('test+'):
        return fake_downloader

    if source.startswith('git+'):
        return git_downloader

    if source.startswith('hg+'):
        return hg_downloader

    if source.startswith('http+'):
        return http_downloader
        
    if 'git' in source:
        return git_downloader

    if 'hg' in source or 'bitbucket' in source:
        return hg_downloader

    raise UpdateError('Unable to choose downloader')

def parse_changelog_file(filename):
    with open(filename) as f:
        return parse_changelog(f.read().decode('utf-8'))


def git_history_extractor(path):
    splitter = '-----======!!!!!!======-----'
    ins = '--!!==!!--'

    with cd(path):
        r = envoy.run('git log --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{splitter}"'.format(ins=ins, splitter=splitter))

        for group in r.std_out.split(splitter)[:-1]:
            _hash, date, msg = group.strip().split(ins)

            r = envoy.run('git checkout {revision}'.format(revision=_hash))
            assert r.status_code == 0
            yield times.parse(date.strip()), msg.strip()


def choose_history_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        def test_history_extractor(path):
            for version, date, message in path:
                yield date, message
        return test_history_extractor

    return git_history_extractor


def python_version_extractor(path):
    return get_package_metadata(path, 'Version')
    

def choose_version_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        index = [0]
        def test_version_extractor(path):
            version = path[index[0]][0]
            index[0] += 1
            return version
        return test_version_extractor

    return python_version_extractor
    

def extract_changelog_from_vcs(path):
    walk_through_history = choose_history_extractor(path)
    extract_version = choose_version_extractor(path)
    current_version = None
    current_commits = []
    results = []

    for date, message in walk_through_history(path):
        version = extract_version(path)

        current_commits.append(message)
        if version != current_version and version is not None:
            current_version = version
            results.append({'version': current_version,
                            'date': date,
                            'sections': [{'items': current_commits}]})
            current_commits = []

    if current_commits:
        results.append({'version': 'x.x.x',
                        'unreleased': True,
                        'date': date,
                        'sections': [{'items': current_commits}]})
    return results


class UpdateError(Exception):
    pass


def search_changelog2(path):
    """Searches a file which contains large
    amount of changelog-like records"""
    
    filenames = search_changelog(path)
    
    raw_data = [(parse_changelog_file(filename), filename)
                for filename in filenames]
    if raw_data:
        raw_data.sort(key=lambda item: len(item[0]),
                      reverse=True)

        filename, raw_data = raw_data[0][1], raw_data[0][0]
        # only return data if we found some records
        if len(raw_data) > 1:
            return filename, raw_data
            
    return None, None
    

def update_changelog(changelog):
    changelog.filename = None

    try:
        download = choose_downloader(changelog)
        path = download(changelog)
    except UpdateError:
        raise
    except Exception:
        logging.getLogger('update-changelog').exception('unhandled')
        raise UpdateError('Unable to download sources')

    try:
        try:
            filename, raw_data = search_changelog2(path)

            if raw_data:
                changelog.filename = os.path.relpath(filename, path)
                changelog.save()
            else:
                raw_data = extract_changelog_from_vcs(path)

        except UpdateError:
            raise
        except Exception:
            logging.getLogger('update-changelog').exception('unhandled')
            raise UpdateError('Unable to parse or extract sources')
            
        if not raw_data:
            raise UpdateError('Changelog not found')

        try:
            update_changelog_from_raw_data(changelog, raw_data)
        except Exception:
            logging.getLogger('update-changelog').exception('unhandled')
            raise UpdateError('Unable to update database')

    finally:
        shutil.rmtree(path)
        changelog.updated_at = timezone.now()
        changelog.save()


def guess_source(namespace, name):
    result = []
    if namespace == 'python':
        response = requests.get('https://pypi.python.org/pypi/' + name)

        urls = re.findall(r'"(https?://.*?)"', response.content)
        for url in urls:
            if ('git' in url or 'bitbucket' in url) and \
               not ('issues' in url or 'gist' in url):
                url, _, _ = normalize_url(url, github_template='https://github.com/{username}/{repo}')
                if url not in result:
                    result.append(url)
    return result

