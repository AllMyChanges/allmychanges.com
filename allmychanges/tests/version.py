from nose.tools import eq_

from allmychanges.version import compare_versions, reorder_versions
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
