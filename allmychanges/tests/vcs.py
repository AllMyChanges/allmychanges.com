# coding: utf-8
import datetime
import re

from nose.tools import eq_
from asserts import sparse_check
from allmychanges.env import Environment
from allmychanges.parsing.pipeline import vcs_processing_pipe
from allmychanges.vcs_extractor import (
    mark_version_bumps,
    _normalize_version_numbers2,
    group_versions)


def _build_tree(tree=None, root=None):
    """
    Tree structure:
    * root (3)
    * 8 (3)
    * 7 (2)
    * 6 (2) # merge
    |\
    | * 5 (1)
    * | 4 (2)
    |/
    * 3 (1)
    * 2 (1)
    * 1 (None)

    Brackets contains discovered version number
    """
    tree = tree or {
        '9': {'version': '3', 'parents': ['8']},
        '8': {'version': '3', 'parents': ['7']},
        '7': {'version': '2', 'parents': ['6']},
        '6': {'version': '2', 'parents': ['4', '5']},
        '5': {'version': '1', 'parents': ['3']},
        '4': {'version': '2', 'parents': ['3']},
        '3': {'version': '1', 'parents': ['2']},
        '2': {'version': '1', 'parents': ['1']},
        '1': {'version': None, 'parents': []},
    }
    root = root or '9'

    for key, item in tree.items():
        item['hash'] = key
        item['message'] = 'Commit ' + key

    tree['root'] = tree[root]

    return tree


def _add_dates(tree):
    date = datetime.date
    for key in tree:
        if key != 'root':
            tree[key]['date'] = date(2014, int(key), 1)


def simplify(version):
    """Returns tuple of version-number, date, list-of-items."""
    return (version.version,
            version.date,
            [re.sub(ur'<span class="changelog-item-type.*?</span>',
                    u'',
                    item['text'])
             for item in version.content[0]])

def test_extract_from_vcs():
    date = datetime.date

    tree = _build_tree()
    _add_dates(tree)
    versions = vcs_processing_pipe(tree)

    sparse_check([
        ('x.x.x',
         None,
         ['Commit 9']),
        ('1',
         date(2014, 2, 1), # version 1 was released with 2nd commit
         ['Commit 2',
          'Commit 1']),
        ('2',
          date(2014, 4, 1), # version 2 was released with 4th commit
          ['Commit 4',
           'Commit 3']),
        ('3',
         date(2014, 8, 1), # version 3 was released with 8th commit
         ['Commit 8',
          'Commit 7',
          # 'Commit 6', this is a merge and it is excluded
          'Commit 5']),
    ], map(simplify, versions))


def test_mark_version_bumps():
    tree = _build_tree()
    _add_dates(tree)
    bumps = mark_version_bumps(tree)
    eq_(['2', '4', '8'], bumps)


def test_mark_version_bumps_when_there_are_gaps():
    # in this case, oldest commit should be considered
    # as a version bump
    # Tree structure:
    # * 5 (1)
    # * 4 (1) # merge
    # |\
    # | * 3 (1)
    # * | 2 (1)
    # |/
    # * 1 (None)

    tree = _build_tree(
        tree={
            '5': {'version': '1',  'parents': ['4']},
            '4': {'version': '1',  'parents': ['2', '3']},
            '3': {'version': '1',  'parents': ['1']},
            '2': {'version': '1',  'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='5')
    _add_dates(tree)
    _normalize_version_numbers2(tree)
    bumps = mark_version_bumps(tree)
    eq_(['2'], bumps)


def test_group_versions():
    tree = _build_tree()
    bumps = ['2', '4', '8']
    versions = group_versions(tree, bumps)
    expected = [
        {'version': '1',
         'messages': ['Commit 2',
                      'Commit 1']},
        {'version': '2',
         'messages': ['Commit 4',
                      'Commit 3']},
        {'version': '3',
         'messages': ['Commit 8',
                      'Commit 7',
                      # 'Commit 6', this is a merge and it is excluded
                      'Commit 5']},
        {'version': 'x.x.x',
         'messages': ['Commit 9'],
         'unreleased': True}]
    sparse_check(expected, versions)


def test_group_versions_when_last_commit_is_a_version_bump():
    # in this case there shouldnt be x.x.x version
    tree = _build_tree(
        tree={
            '2': {'version': '1', 'parents': ['1']},
            '1': {'version': None, 'parents': []},
        },
        root='2')

    bumps = ['2']
    versions = group_versions(tree, bumps)
    expected = [
        {'version': '1',
         'messages': ['Commit 2',
                      'Commit 1']}]
    sparse_check(expected, versions)


def test_ignore_vcs_versions_if_there_is_only_one_unreleased_version():
    date = datetime.date
    versions = vcs_processing_pipe(
        [(None, date(2014, 1, 15), 'Initial commit'),
         (None, date(2014, 1, 15), 'Feature was added'),
         (None, date(2014, 1, 16), 'Tests were added')])
    eq_([], versions)
