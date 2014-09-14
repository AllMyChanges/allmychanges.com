import anyjson
import datetime
import copy
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
import sys
import setuptools as orig_setuptools

from lxml import html
from contextlib import contextmanager

from django.conf import settings
from django.utils.encoding import force_text
from django.utils import timezone

from allmychanges.crawler import search_changelog, parse_changelog, _extract_date


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
        regex = r'[/:](?P<username>[A-Za-z0-9-_]+)/(?P<repo>.*?)(?:\.git|/|$)'
        match = re.search(regex, url)
        if match is not None:
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

    if re.search(r'cve-\d+-\d+', commit_message) is not None:
        return 'sec'
    elif 'backward incompatible' in commit_message:
        return 'inc'
    elif 'deprecated' in commit_message:
        return 'dep'
    elif commit_message.startswith('add'):
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
    raw_html = _render_text_for_markup_type(text, markup_type=markup_type)
    return get_clean_text_from_html(raw_html)


def _render_text_for_markup_type(text, markup_type):
    if markup_type == 'markdown':
        return _render_markdown(text)
    elif markup_type == 'rest':
        return _render_rest(text)
    else:
        return text


def _render_markdown(text):
    if text is None:
        text = ''
    return markup.markdown(force_text(text))


def _render_rest(text):
    if text is None:
        text = ''
    return markup.restructuredtext(force_text(text))


def graphite_send(**kwargs):
    try:
        g = graphitesend.init(prefix=settings.GRAPHITE_PREFIX,
                              system_name='',
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


def discard_seconds(dt):
    return datetime.datetime(*dt.timetuple()[:5])


# TODO: remove
def fill_missing_dates(raw_data):
    """Algorithm.

    If first item has no date, then it is today.
    If Nth item has date, then assume it is a current_date.
    If Nth item has no date and we have current_date, then assume item's
    date is current_date.
    If Nth item has no date and we have no current_date, then assume, it
    is a now() - month and act like we have it.
    """
    result = []
    today = discard_seconds(datetime.datetime.utcnow())
    month = datetime.timedelta(30)
    current_date = None

    for idx, item in enumerate(reversed(raw_data)):
        item = copy.deepcopy(item)
        has_date = item.get('date')

        if not has_date:
            if idx == 0:
                item['discovered_at'] = today
            else:
                if current_date is not None:
                    item['discovered_at'] = current_date
                else:
                    item['discovered_at'] = today - month
        else:
            current_date = item['date']
            item['discovered_at'] = current_date
        result.append(item)

    result.reverse()
    return result


def fill_missing_dates2(raw_data):
    """Algorithm.

    If first item has no date, then it is today.
    If Nth item has date, then assume it is a current_date.
    If Nth item has no date and we have current_date, then assume item's
    date is current_date.
    If Nth item has no date and we have no current_date, then assume, it
    is a now() - month and act like we have it.
    """
    result = []
    today = discard_seconds(datetime.datetime.utcnow())
    month = datetime.timedelta(30)
    current_date = None

    for idx, item in enumerate(reversed(raw_data)):
        item = copy.deepcopy(item)
        has_date = getattr(item, 'date', None)

        if not has_date:
            if idx == 0:
                item.discovered_at = today
            else:
                if current_date is not None:
                    item.discovered_at = current_date
                else:
                    item.discovered_at = today - month
        else:
            current_date = item.date
            item.discovered_at = current_date
        result.append(item)

    result.reverse()
    return result


def update_changelog_from_raw_data(changelog, raw_data, code_version='v1', preview_id=None, from_vcs=False):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""

    if changelog.versions.count() == 0:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates(raw_data)

    for raw_version in raw_data:
        if not raw_version['sections']:
            # we skipe versions without description
            # because some maintainers use these to add
            # unreleased versions into the changelog.
            # Example: https://github.com/kraih/mojo/blob/master/Changes
            continue

        version, created = changelog.versions.get_or_create(
            number=raw_version['version'],
            unreleased=raw_version.get('unreleased', False),
            code_version=code_version)

        if from_vcs:
            version.filename = 'VCS'

        version.date = raw_version.get('date')
        version.preview_id = preview_id

        if version.discovered_at is None:
            version.discovered_at = raw_version.get('discovered_at', timezone.now())

        version.save()

        version.sections.all().delete()
        for raw_section in raw_version['sections']:
            section = version.sections.create(notes=raw_section.get('notes'),
                                              code_version=code_version)
            for raw_item in raw_section.get('items', []):
                section.items.create(text=raw_item, type=get_commit_type(raw_item))


def update_changelog_from_raw_data2(changelog, raw_data, preview_id=None):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    code_version = 'v2'

    if changelog.versions.filter(code_version=code_version).count() == 0:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates2(raw_data)

    for raw_version in raw_data:
        version, created = changelog.versions.get_or_create(
            number=raw_version.version,
            code_version=code_version)

        version.unreleased = getattr(raw_version, 'unreleased', False)
        version.filename = getattr(raw_version, 'filename', None)
        version.date = getattr(raw_version, 'date', None)
        version.preview_id = preview_id

        if version.discovered_at is None:
            version.discovered_at = getattr(raw_version, 'discovered_at', timezone.now())

        version.save()

        version.sections.all().delete()
        for raw_section in raw_version.content:
            if isinstance(raw_section, list):
                section = version.sections.create(code_version=code_version)
                for raw_item in raw_section:
                    section.items.create(text=raw_item['text'],
                                         type=raw_item['type'])
            else:
                section = version.sections.create(notes=raw_section,
                                                  code_version=code_version)


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


def git_downloader(source):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url, username, repo_name = normalize_url(source)

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


def choose_downloader(source):
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
    """This function should always return a list.
    """
    with open(filename) as f:
        text = f.read()
        try:
            decoded = text.decode('utf-8')
        except UnicodeDecodeError:
            return []
        else:
            return parse_changelog(decoded)


def git_history_extractor(path):
    splitter = '-----======!!!!!!======-----'
    ins = '--!!==!!--'

    with cd(path):
        r = envoy.run('git log --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{splitter}"'.format(ins=ins, splitter=splitter))

        for group in r.std_out.split(splitter)[:-1]:
            _hash, date, msg = group.strip().split(ins)

            r = envoy.run('git checkout {revision}'.format(revision=_hash))
            assert r.status_code == 0
            yield _extract_date(date.strip()), msg.strip('\n -')


def choose_history_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        def test_history_extractor(path):
            for version, date, message in path:
                yield date, message
        return test_history_extractor

    return git_history_extractor


def python_version_extractor(path):
    if os.path.exists(os.path.join(path, 'setup.py')):
        if os.path.exists(os.path.join(path, 'setup.pyc')):
            os.unlink(os.path.join(path, 'setup.pyc'))

        try:
            metadata = {}

            class FakeSetuptools(object):
                def setup(self, *args, **kwargs):
                    metadata.update(kwargs)

                def __getattr__(self, name):
                    return getattr(orig_setuptools, name)

            sys.modules['distutils.core'] = FakeSetuptools()
            sys.modules['setuptools'] = FakeSetuptools()
            sys.path.insert(0, path)

            try:
                from setup import setup
            except Exception:
                pass

            return metadata.get('version')
        finally:
            if sys.path[0] == path:
                sys.path.pop(0)

            for name in ('distutils.core', 'setuptools', 'setup'):
                if name in sys.modules:
                    del sys.modules[name]


def npm_version_extractor(path):
    filename = os.path.join(path, 'package.json')

    if os.path.exists(filename):
        with open(filename) as f:
            try:
                data = anyjson.deserialize(f.read())
                return data.get('version')
            except Exception:
                pass


def choose_version_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        index = [0]
        def test_version_extractor(path):
            version = path[index[0]][0]
            index[0] += 1
            return version
        return test_version_extractor

    if os.path.exists(os.path.join(path, 'setup.py')):
        return python_version_extractor

    if os.path.exists(os.path.join(path, 'package.json')):
        return npm_version_extractor

    # TODO: raise exception because we unable to extract versions
    null_extractor = lambda path: None
    return null_extractor


def extract_changelog_from_vcs(path):
    walk_through_history = choose_history_extractor(path)
    extract_version = choose_version_extractor(path)
    current_version = None
    current_commits = []
    results = []

    for date, message in walk_through_history(path):
        version = extract_version(path)

        if message:
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

    if len(results) < 2:
        raise UpdateError('Unable to extract versions from VCS history')

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
        if len(raw_data) > 1 or 'changelog' in filename.lower():
            return filename, raw_data

    return None, None


def update_changelog(changelog, preview_id=None):
    changelog.filename = None

    if preview_id is None:
        ignore_list = changelog.get_ignore_list()
        check_list = changelog.get_check_list()
        source = changelog.source
    else:
        preview = changelog.previews.get(pk=preview_id)
        ignore_list = preview.get_ignore_list()
        check_list = preview.get_check_list()
        source = preview.source


    try:
        download = choose_downloader(source)
        path = download(source)
    except UpdateError:
        raise
    except Exception:
        logging.getLogger('update-changelog').exception('unhandled')
        raise UpdateError('Unable to download sources')

    try:
        try:
            from allmychanges.parsing.pipeline import processing_pipe
            versions = processing_pipe(path,
                                       ignore_list,
                                       check_list)
            if versions:
                update_changelog_from_raw_data2(changelog, versions, preview_id=preview_id)
            else:
                logging.getLogger('update-changelog2').debug('updating v2 from vcs')
                raw_data = extract_changelog_from_vcs(path)
                update_changelog_from_raw_data(changelog, raw_data, code_version='v2', preview_id=preview_id, from_vcs=True)

        except Exception:
            logging.getLogger('update-changelog2').exception('unhandled')

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
            update_changelog_from_raw_data(changelog, raw_data, preview_id=preview_id)
        except Exception:
            logging.getLogger('update-changelog').exception('unhandled')
            raise UpdateError('Unable to update database')

    finally:
        shutil.rmtree(path)

        # we only need to change updated_at if this
        # wasn't preview update
        if preview_id is None:
            changelog.updated_at = timezone.now()
            changelog.save()


def dt_in_window(tz, system_time, hour):
    local = times.to_local(system_time, tz)
    return local.hour == hour


def parse_ints(text):
    """Parses text with comma-separated list of integers
    and returns python list of itegers."""
    return map(int, filter(None, text.split(',')))


def join_ints(ints):
    """Joins list of intergers into the ordered comma-separated text.
    """
    return ','.join(map(str, sorted(ints)))
