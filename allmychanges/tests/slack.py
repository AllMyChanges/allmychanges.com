# coding: utf-8

from nose.tools import eq_

from allmychanges.notifications.slack import (
    convert_md_links,
    convert_md_bolds,
)


def test_convert_links():
    text = ('add one-way binding to the isolate scope definition '
            '([4ac23c0a](https://github.com/angular/angular.js/commit/4ac23c0ac59c269d65b7f78efec75d060121bd18)\n'
            '[#13928](https://github.com/angular/angular.js/issues/13928))')
    expected = ('add one-way binding to the isolate scope definition '
                '(<https://github.com/angular/angular.js/commit/4ac23c0ac59c269d65b7f78efec75d060121bd18|4ac23c0a>\n'
                '<https://github.com/angular/angular.js/issues/13928|#13928>)')

    eq_(expected, convert_md_links(text))


def test_convert_bolds():
    text =      '* **$parse:** Copy `inputs` for expressions with expensive checks'
    expected =  '* *$parse:* Copy `inputs` for expressions with expensive checks'
    eq_(expected, convert_md_bolds(text))

    text = '* **dateFilter, input:** fix Date parsing in IE/Edge when timezone offset'
    expected= '* *dateFilter, input:* fix Date parsing in IE/Edge when timezone offset'
    eq_(expected, convert_md_bolds(text))
