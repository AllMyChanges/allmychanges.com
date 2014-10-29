import anyjson
import envoy
import os.path
import setuptools as orig_setuptools
import sys


from allmychanges.utils import cd
from allmychanges.crawler import _extract_date
from allmychanges.exceptions import UpdateError


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
