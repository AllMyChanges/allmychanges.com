import random

from nose.tools import eq_

from allmychanges.version import (
    compare_versions,
    reorder_versions,
    version_update_has_wrong_order,
    has_hole,
    follows,
    on_same_branch,
    find_branches)
from allmychanges.models import Version
from allmychanges.tests.utils import refresh


def test_version_comparison():
    # 0.8.2-beta < 0.8.2
    eq_(-1, compare_versions('0.8.2-beta', '0.8.2'))
    # 0.8.1 < 0.8.2-beta
    eq_(-1, compare_versions('0.8.1', '0.8.2-beta'))
    # 0.8.2-alfa < 0.8.2-beta
    eq_(-1, compare_versions('0.8.2-alpha', '0.8.2-beta'))

    # 0.8 < 0.8.1
    eq_(-1, compare_versions('0.8', '0.8.1'))
    # 0.8-alpha < 0.8.1-alpha
    eq_(-1, compare_versions('0.8-alpha', '0.8.1-alpha'))

    # simple case
    eq_(-1, compare_versions('1.2.1', '1.2.3'))

    # weird case compared lexicographically
    eq_(-1, compare_versions('2008g', '2014.10'))


def test_reorder_versions():
    # changelog = Changelog.objects.create(
    #     namespace='python', name='pip', source='test+samples/very-simple.md')
    v1 = Version.objects.create(number='1.2.3')
    v2 = Version.objects.create(number='1.3')
    v3 = Version.objects.create(number='1.0b1')

    reorder_versions([v1, v2, v3])
    v1 = refresh(v1)
    v2 = refresh(v2)
    v3 = refresh(v3)

    eq_(0, v3.order_idx)
    eq_(1, v1.order_idx)
    eq_(2, v2.order_idx)


def test_find_branches_primitive():
    versions = []
    branches = []
    eq_(branches, find_branches(versions))

    versions = ['0.1.0']
    branches = ['0.1.0']
    eq_(branches, find_branches(versions))


def test_find_branches_simple():
    versions = ['0.1.0', '0.1.1']
    branches = ['0.1.1']
    eq_(branches, find_branches(versions))


def test_find_branches():
    versions = ['0.1.0', '0.1.1', '0.2.0', '0.3.0', '0.3.1', '0.4.0']
    branches = ['0.1.1', '0.3.1', '0.4.0']
    eq_(branches, find_branches(versions))


def test_find_branches_when_unsorted():
    versions = ['0.1.0', '0.1.1', '0.2.0', '0.3.0', '0.3.1', '0.4.0']
    random.shuffle(versions)

    branches = ['0.1.1', '0.3.1', '0.4.0']
    eq_(branches, find_branches(versions))


def test_wrong_order_primitive():
    versions = []
    new_versions = ['0.1.0']
    eq_(False, version_update_has_wrong_order(versions, new_versions))


def test_wrong_order_simple():
    versions = ['0.1.0']
    new_versions = ['0.1.1', '0.1.2', '0.2.0']
    eq_(False, version_update_has_wrong_order(versions, new_versions))


def test_wrong_order_bad():
    versions = ['0.1.0']
    new_versions = ['0.2.0']
    eq_(False, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.1.1']
    eq_(False, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.1.2'] # 0.1.1 is absent
    eq_(True, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.3.0'] # 0.2.0 is absent
    eq_(True, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.2.1'] # 0.2.0 is absent
    eq_(True, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.2.0', '0.4.0'] # 0.3.0 is absent
    eq_(True, version_update_has_wrong_order(versions, new_versions))

    versions = ['0.1.0']
    new_versions = ['0.1.2'] # 0.1.1 is absent
    eq_(True, version_update_has_wrong_order(versions, new_versions))


def test_on_the_same_branch():
    eq_(True, on_same_branch('1.8.1', '1.8.2'))
    eq_(True, on_same_branch('1.8.1', '1.8.3'))
    eq_(True, on_same_branch('1.8.1', '1.8.1-rc1'))
    eq_(True, on_same_branch('1.8.1', '1.8.4-rc1'))
    eq_(False, on_same_branch('1.8.1', '1.9.0'))
    eq_(False, on_same_branch('1.8.1', '1.9.0-rc1'))
    eq_(False, on_same_branch('1.8.1', '2.8.1'))


def test_wrong_order_complex():
    versions = ['1.8.0', '1.8.1', '1.9.0']
    new_versions = ['1.8.2', '1.9.1', '1.9.2']
    eq_(False, version_update_has_wrong_order(versions, new_versions))

    versions = ['1.8.0', '1.8.1', '1.9.0']
    new_versions = ['1.8.2', '1.9.1', '1.9.2', '1.10.0']
    eq_(False, version_update_has_wrong_order(versions, new_versions))

    versions = ['1.8.0', '1.8.1', '1.9.0']
    new_versions = ['1.8.2', '1.9.2'] # version 1.9.1 is missing
    eq_(True, version_update_has_wrong_order(versions, new_versions))


def test_follows():
    eq_(True, follows('0.1.0', '0.1.1'))
    eq_(True, follows('0.1.0', '0.2.0'))
    eq_(True, follows('0.1.1', '0.2.0'))
    eq_(False, follows('0.1.1', '0.2.1'))
    eq_(False, follows('0.1.0', '0.1.2'))
    eq_(False, follows('0.1.0', '0.2.1'))
    eq_(False, follows('0.2.0', '0.1.0'))
    eq_(False, follows('0.1.1', '0.1.0'))
    eq_(True, follows('1.0.0-rc1', '1.0.0-rc2'))
    eq_(False, follows('1.0.0-rc1', '1.0.0-rc3'))


def test_hole():
    eq_(False, has_hole(['0.1.0', '0.2.0']))
    eq_(False, has_hole(['0.1.0', '0.1.1', '0.2.0']))
    eq_(True, has_hole(['0.2.0', '0.4.0']))
