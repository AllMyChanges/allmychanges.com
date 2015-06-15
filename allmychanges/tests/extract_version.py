from nose.tools import eq_
from allmychanges.crawler import _extract_version


def test_bad_lines():
    eq_(None, _extract_version('des-cbc           3624.96k     5258.21k     5530.91k     5624.30k     5628.26k'))


def test_good_lines():
    eq_('0.9.2b', _extract_version('Version 0.9.2b  [22 Mar 1999]'))
