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

    def gen_checkouter(hash_):
        def checkout():
            command = 'git reset --hard {revision}'.format(revision=hash_)
            with cd(path):
                r = envoy.run(command)
                assert r.status_code == 0, 'git checkout returned code {0} and here is it\'s stderr:{1}'.format(
                    r.status_code, r.std_err)
            return path
        return checkout

    with cd(path):
        r = envoy.run('git log --simplify-merges --no-merges --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{splitter}"'.format(ins=ins, splitter=splitter))

        # containse tuples (_hash, date, msg)
        groups = (group.strip().split(ins)
                  for group in r.std_out.split(splitter)[:-1])
        return [[_extract_date(date.strip()),
                 msg.strip('\n -'),
                 gen_checkouter(_hash.strip())]
                for _hash, date, msg in groups]




def choose_history_extractor(path):
    if isinstance(path, list):
        # this is a special case for tests
        def test_history_extractor(path):
            return [[date,
                     message,
                     (lambda version :lambda: version)(version)]
                    for version, date, message in path]
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
        def test_version_extractor(path):
            return path
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

    get_history = choose_history_extractor(path)
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

    def add_version_number(commit):
        if len(commit) == 3:
            date, message, checkout = commit
            checkout_path = checkout()
            version = extract_version(checkout_path)
            commit.append(version)
        return commit[-1]

    def rec(commits):
        left_version = commits[0][-1]
        right_version = add_version_number(commits[-1])

        if len(commits) == 2:
            if right_version is None:
                commits[-1][-1] = left_version
        else:
            if left_version == right_version:
                for commit in commits[1:-1]:
                    commit.append(left_version)
            else:
                threshold = len(commits) / 2
                rec(commits[:threshold + 1])
                rec(commits[threshold:])

    commits = get_history(path)

    if commits:
#        ver = 'old'
        ver = 'new' # use new fast algotithm of version searching

        if ver == 'new':
            # first, we'll skip heading commits without version number
            idx = 0
            number = add_version_number(commits[idx])

            while number is None:
                idx += 1
                number = add_version_number(commits[idx])

            rec(commits[idx:])

        if ver == 'old':
            for commit in commits:
                number = add_version_number(commit)

        from collections import defaultdict
        already_seen = defaultdict(int)
        previous_number = None

        # We need this step to normalize version order
        # because sometimes after the merge it is currupted
        for commit in commits:
            number = commit[-1]
            if number is not None and previous_number is not None and number != previous_number and number in already_seen:
                # fixing commit merged after the version
                # was bumped
                commit[-1] = previous_number
            else:
                already_seen[number] += 1
                previous_number = number

        for date, message, get_version, version in commits:
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
