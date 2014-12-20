import anyjson
import envoy
import os.path
import setuptools as orig_setuptools
import sys


from allmychanges.utils import cd
from allmychanges.crawler import _extract_date

from twiggy_goodies.threading import log


def git_history_extractor(path):
    splitter = '-----======!!!!!!======-----'
    ins = '--!!==!!--'

    with cd(path):
        r = envoy.run('git log --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{splitter}"'.format(ins=ins, splitter=splitter))

        for group in r.std_out.split(splitter)[:-1]:
            _hash, date, msg = group.strip().split(ins)

            command = 'git reset --hard {revision}'.format(revision=_hash)
            r = envoy.run(command)
            assert r.status_code == 0, 'git checkout returned code {0} and here is it\'s stderr:{1}'.format(
                r.status_code, r.std_err)
            yield _extract_date(date.strip()), msg.strip('\n -'), _hash


def choose_history_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        def test_history_extractor(path):
            for version, date, message in path:
                yield date, message, version
        return test_history_extractor

    return git_history_extractor


def python_version_extractor(path, use_threads=True):
    from multiprocessing import Process, Queue
    from collections import deque

    if use_threads:
        queue = Queue()
        process = Process(target=python_version_extractor_worker,
                          args=(path, queue))
        process.start()
        process.join()
        return queue.get()
    else:
        class Queue(deque):
            def put(self, value):
                self.append(value)
            def get(self):
                return self.popleft()
        queue = Queue()
        python_version_extractor_worker(path, queue)
        return queue.get()


def python_version_extractor_worker(path, queue):
    with cd(path):
        if os.path.exists('setup.py'):
            envoy.run("find . -name '*.pyc' -delete")

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
                except:
                    pass

                version = metadata.get('version')
                queue.put(version)
            finally:
                pass
    queue.put(None)


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


def get_versions_from_vcs(env):
    path = env.dirname

    walk_through_history = choose_history_extractor(path)
    extract_version = choose_version_extractor(path)
    current_version = None
    current_commits = []

    def create_version(date, unreleased=False):
        return env.push(type='almost_version',
                        title=current_version,
                        version=current_version,
                        filename='VCS',
                        date=None if unreleased else date,
                        unreleased=unreleased,
                        content=[current_commits])

    for date, message, revision in walk_through_history(path):
        version = extract_version(path)

        if message:
            current_commits.append(message)

        if version != current_version and version is not None:
            current_version = version
            yield create_version(date)
            current_commits = []

    if current_commits:
        current_version = 'x.x.x'
        yield create_version(date, unreleased=True)


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
        return []

    return results
