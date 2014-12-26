import anyjson
import envoy
import os
import os.path
import setuptools as orig_setuptools
import sys
import itertools

from collections import defaultdict
from orderedset import OrderedSet
from allmychanges.utils import cd, trace
from allmychanges.crawler import _extract_date
from django.core.cache import cache

from twiggy_goodies.threading import log


def git_history_extractor(path, limit=None):
    """Returns list of dicts starting from older commits to newer.
    Each dict should contain fields: `date`, `message`, `hash`, `checkout`,
    where `checkout` is a function which makes checkout of this version
    and returns path which will be passed to the version extractor.
    Optionally, dict could contain `version` field, taken from tag.
    """
    splitter = '-----======!!!!!!======-----'
    ins = '--!!==!!--'

    def do(command):
#        print 'EXEC>', command
        r = envoy.run(command)
        assert r.status_code == 0, '"{0} returned code {1} and here is it\'s stderr:{2}'.format(
            command, r.status_code, r.std_err)
        return r

    with cd(path):
        branch = do('git rev-parse --abbrev-ref HEAD').std_out.strip()

        def gen_checkouter(hash_):
            def checkout():
                with cd(path):
                    # do('git reset --hard {revision}'.format(revision=hash_))
                    # if hash_.startswith('753cb358'):
                    #     import pdb; pdb.set_trace()

                    merge_point = do('git rev-list {hash}..{branch} --ancestry-path --merges --reverse'.format(
                        hash=hash_,
                        branch=branch)).std_out.split('\n', 1)[0]

                    do('git reset --hard')
                    do('git checkout ' + hash_)
    #                 if merge_point:
    #                     do('git checkout ' + merge_point)
    # #                    do('git branch -D vcs-checkout || true')
    # #                    do('git checkout -b vcs-checkout')
    #     #                do('git reset --hard {revision}'.format(revision=hash_))
    # #                    do('git merge ' + hash_)
    #                 else:
    #                     do('git checkout ' + hash_)
                return path
            return checkout

        r = envoy.run('git log --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{ins}%n%P%n{splitter}"'.format(ins=ins, splitter=splitter))
#        r = envoy.run('git log --simplify-merges --no-merges --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{ins}%n%P%n{splitter}"'.format(ins=ins, splitter=splitter))
#        r = envoy.run('git log --simplify-merges --reverse --pretty=format:"%H%n{ins}%n%ai%n{ins}%n%B%n{splitter}"'.format(ins=ins, splitter=splitter))

        # containse tuples (_hash, date, msg, parents)
        groups = (group.strip().split(ins)
                  for group in r.std_out.split(splitter)[:-1])
        result = (dict(date=_extract_date(date.strip()),
                       message=msg.strip('\n -'),
                       checkout=gen_checkouter(_hash.strip()),
                       hash=_hash.strip(),
                       parents=parents.split())
                  for _hash, date, msg, parents in groups)
        if limit:
            result = itertools.islice(result, 0, limit)
        result = list(result)

        root = result[0]['hash']

        result = dict((item['hash'], item) for item in result)
        result['root'] = result[root]
        del result[root]
        return result


def choose_history_extractor(path):
    if isinstance(path, dict):
        # this is a special case for tests
        def test_history_extractor(path):
            def create_version(item):
                new_item = item.copy()
                new_item['checkout'] = lambda: item['version']
                del new_item['version']
                return new_item
            return dict((key, create_version(item))
                        for key, item in path.items())

            # return [[date,
            #          message,
            #          (lambda version :lambda: version)(version)]
            #         for version, date, message in path]
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
    if isinstance(path, dict):
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


def stop_at_hash_if_needed(hash):
    if os.environ.get('STOP_AT_HASH'):
        hashes = os.environ['STOP_AT_HASH'].split(',')
        for hash_to_check in hashes:
            if hash.startswith(hash_to_check):
                import pdb; pdb.set_trace()


ver_num_calls = 0
def _add_version_number(commit, extract_version):
    global ver_num_calls

    if 'version' not in commit:
        cache_key = 'version:' + commit['hash']
        version = cache.get(cache_key)
        if not version:
            ver_num_calls += 1
            stop_at_hash_if_needed(commit['hash'])
            checkout_path = commit['checkout']()
            version = extract_version(checkout_path)
            cache.set(cache_key, version, 60 * 60 * 24)

        commit['version'] = version
    return commit['version']


# TODO we don't need it anymore
def _normalize_version_numbers(commits):
    already_seen = defaultdict(int)
    previous_number = None

    # We need this step to normalize version order
    # because sometimes after the merge it is currupted
    stop_at_hash = os.environ.get('STOP_AT_HASH')

    for commit in commits:
        number = commit['version']
        if number is not None and previous_number is not None and number != previous_number and number in already_seen:
            # fixing commit merged after the version
            # was bumped
            if stop_at_hash and commit['hash'].startswith(stop_at_hash):
                import pdb; pdb.set_trace()

            commit['version'] = previous_number
        else:
            already_seen[number] += 1
            previous_number = number

def write_vcs_versions_bin(commits, extract_version):
    # first, we'll skip heading commits without version number
    stop_at_hash = os.environ.get('STOP_AT_HASH')
    idx = 0
    number = _add_version_number(commits[idx], extract_version)

    while number is None:
        idx += 1
        number = _add_version_number(commits[idx], extract_version)

    # and now we need to go through the history recursivly
    # dividing it twice on each step
    def rec(commits, extract_version):
        left_version = commits[0]['version']
        right_version = _add_version_number(commits[-1], extract_version)

        if len(commits) == 2:
            if right_version is None:
                commits[-1]['version'] = left_version
        else:
            if left_version == right_version:
                for commit in commits[1:-1]:
                    if stop_at_hash and commit['hash'].startswith(stop_at_hash):
                        import pdb; pdb.set_trace()
                    commit['version'] = left_version
            else:
                threshold = len(commits) / 2
                rec(commits[:threshold + 1], extract_version)
                rec(commits[threshold:], extract_version)

    rec(commits[idx:], extract_version)
    _normalize_version_numbers(commits)


def _normalize_version_numbers2(commits):
    for commit in commits.values():
        if 'version' not in commit:
            import pdb; pdb.set_trace()

        if commit['version'] is None:
            to_update = deque()
            to_check = deque()
            current = commit
            while current:
                if current['version'] is not None:
                    for commit in to_update:
                        commit['version'] = current['version']
                    break
                else:
                    to_update.append(current)
                    to_check.extend(filter(None,
                                           map(commits.get,
                                               current['parents'])))
                    try:
                        current = to_check.popleft()
                    except Exception:
                        current = None

import time

def write_vcs_versions_slowly(commits, extract_version):
    start = time.time()
    for idx, commit in enumerate(commits.values()):
        delta = (time.time() - start)
        if delta > 5:
            print float(idx) / delta, 'per second'
        _add_version_number(commit, extract_version)

    _normalize_version_numbers2(commits)


def write_vcs_versions_bin_helper(commits, extract_version):
    # first, we'll skip commits from head and tail without version numbers
    number = _add_version_number(commits[0], extract_version)
    while number is None:
        commits = commits[1:]
        if not commits:
            break
        number = _add_version_number(commits[0], extract_version)

    if not commits:
        return

    number = _add_version_number(commits[-1], extract_version)
    while number is None:
        commits = commits[:-1]
        if not commits:
            break
        number = _add_version_number(commits[-1], extract_version)

    if not commits:
        return

    # and now we need to go through the history recursivly
    # dividing it twice on each step
    def rec(commits, extract_version):
        left_version = commits[0]['version']
        right_version = _add_version_number(commits[-1], extract_version)

        if len(commits) == 2:
            if right_version is None:
                commits[-1]['version'] = left_version
        else:
            if left_version == right_version:
                for commit in commits[1:-1]:
                    commit['version'] = left_version
            else:
                threshold = len(commits) / 2
                rec(commits[:threshold + 1], extract_version)
                rec(commits[threshold:], extract_version)

    rec(commits, extract_version)



def write_vcs_versions_fast(commits, extract_version):
    queue = deque()
    commit = commits['root']
    print 'writing vcs versions'

    covered = set()

    def enque(hash):
        if hash not in covered:
            commit = commits.get(hash)
            if commit is not None:
                queue.append(commit)


    start = time.time()

    while commit:
        delta = (time.time() - start)
        if delta > 5:
            print float(len(covered)) / delta, 'per second', 'queue:', len(queue), 'processed:', len(covered), 'ver_num_calls:', ver_num_calls

        #version = _add_version_number(commit, extract_version)
        # fast forward
        commits_between = []
        # a hack to reuse version number from a previously calculated commit
        if 'child' in commit:
            commits_between.append(commit['child'])
        limit = 200
        forward = commit
        while forward['hash'] not in covered and limit > 0:
            covered.add(forward['hash'])
            commits_between.append(forward)

            num_parents = len(forward['parents'])
            if num_parents > 1:
                map(enque, forward['parents'][1:])
                for it_hash in forward['parents'][1:]:
                    it_commit = commits.get(it_hash)
                    if it_commit:
                        it_commit['child'] = forward
            if num_parents > 0:
                forward = commits[forward['parents'][0]]

            limit -= 1

        covered.add(forward['hash'])
        # we add this point nonetheless it could be already covered
        # because if it is covered, then we don't need to calculate
        # version number again
        commits_between.append(forward)

        write_vcs_versions_bin_helper(commits_between, extract_version)
        map(enque, forward['parents'])

        try:
            commit = queue.pop()
        except IndexError:
            print 'Exit'
            commit = None

    _normalize_version_numbers2(commits)


def get_versions_from_vcs(env):
    path = env.dirname

    get_history = choose_history_extractor(path)
    extract_version = choose_version_extractor(path)
    # current_version = None
    # current_commits = []

    # def create_version(date, unreleased=False):
    #     return env.push(type='almost_version',
    #                     title=current_version,
    #                     version=current_version,
    #                     filename='VCS',
    #                     date=None if unreleased else date,
    #                     unreleased=unreleased,
    #                     content=[current_commits])

    commits = get_history(path)

    write_vcs_versions_fast(commits, extract_version)
    bumps = mark_version_bumps(commits)
    grouped = group_versions(commits, bumps)
    for version in grouped:
        yield env.push(type='almost_version',
                        title=version['version'],
                        version=version['version'],
                        filename='VCS',
                        date=None if version.get('unreleased') else version['date'],
                        unreleased=version.get('unreleased'),
                        content=[version['messages']])

    if False: # TODO: remove this old code
        ver = 'old'
#        ver = 'new' # use new fast algotithm of version searching

        if ver == 'new':
            write_vcs_versions_bin(commits, extract_version)
        else:
            write_vcs_versions_slowly(commits, extract_version)

        for commit in commits:
            message = commit['message']
            version = commit['version']
            date = commit['date']

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


import operator
from collections import deque

def mark_version_bumps(tree):
    bumps = []
    queue = deque()
    processed = set()
    commit = tree['root']

    while commit:
        hash = commit['hash']
        if hash not in processed:
            stop_at_hash_if_needed(hash)

            version = commit['version']
            if version is not None:
                parents = map(tree.get, commit['parents'])
                # if history was limited, then some parents could be unavailable
                parents = filter(None, parents)
                if not any(map(lambda parent: parent['version'] == version,
                   parents)):
                    bumps.append(hash)

                queue.extend(parents)
            processed.add(hash)
        try:
            commit = queue.popleft()
        except IndexError:
            commit = None
    return list(reversed(bumps))


def mark_version_bumps_rec(tree):
    """Returns hashes of commits where
    version changes.
    """
    @trace
    def rec(commit, cache={}):
        hash = commit['hash']
        if hash in cache:
            return cache[hash]

        version = commit['version']
        parents = map(tree.get, commit['parents'])

        parent_bumps = reduce(operator.__or__,
                              (rec(parent, cache=cache) for parent in parents),
                              OrderedSet())

        if not any(map(lambda parent: parent['version'] == version,
                   parents)):
            if version:
                cache[hash] =  parent_bumps | OrderedSet([hash])
                return cache[hash]

        cache[hash] = parent_bumps
        return cache[hash]


    return rec(tree['root'])


from itertools import chain

def group_versions(tree, bumps):
    bumps = bumps + ['root']

    processed = set()
    def collect_messages(commit):
        if commit['hash'] in processed:
            return []

        if len(commit['parents']) > 1:
            messages = []
        else:
            messages = [commit['message']]

        parents = map(tree.get, commit['parents'])
        parent_messages = map(collect_messages, parents)
        processed.add(commit['hash'])
        return messages + list(chain(*parent_messages))

    result = []

    for bump in bumps:
        commit = tree[bump].copy()
        commit['messages'] = collect_messages(commit)
        del commit['message']
        result.append(commit)

    result[-1]['version'] = 'x.x.x'
    result[-1]['unreleased'] = True
    return result
