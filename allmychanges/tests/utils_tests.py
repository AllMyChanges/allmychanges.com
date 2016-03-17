# coding: utf-8

import datetime

from nose.tools import eq_
from allmychanges.utils import (
    ensure_datetime,
    parse_search_list,
)


def test_ensure_datetime():
    date = datetime.date(2016, 3, 15)
    assert isinstance(ensure_datetime(date), datetime.datetime)


def test_parse_search_list_ignores_lists():
    items = ['blah', 'minor']
    eq_(items, parse_search_list(items))
