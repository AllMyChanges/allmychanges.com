# coding: utf-8

from nose.tools import eq_

from allmychanges.notifications.slack import (
    convert_md_links,
    convert_md_bolds,
    convert_md_images,
)


def test_convert_links():
    text = ('add one-way binding to the isolate scope definition '
            '([4ac23c0a](https://github.com/angular/angular.js/commit/4ac23c0ac59c269d65b7f78efec75d060121bd18)\n'
            '[#13928](https://github.com/angular/angular.js/issues/13928))')
    expected = ('add one-way binding to the isolate scope definition '
                '(<https://github.com/angular/angular.js/commit/4ac23c0ac59c269d65b7f78efec75d060121bd18|4ac23c0a>\n'
                '<https://github.com/angular/angular.js/issues/13928|#13928>)')

    eq_(expected, convert_md_links(text))

    text = '[Full Changelog](https://github.com/omab/python-social-auth/compare/v0.2.13...v0.2.14)'
    expected = '<https://github.com/omab/python-social-auth/compare/v0.2.13...v0.2.14|Full Changelog>'

    eq_(expected, convert_md_links(text))

    text = '  * **$route:** allow route reload to be prevented ([2f0a50b5](https://github.com/angular/angular.js/commit/2f0a50b526c5d0263879d3e845866e1af6fd9791), [#9824](https://github.com/angular/angular.js/issues/9824), [#13894](https://github.com/angular/angular.js/issues/13894))'
    expected = '  * **$route:** allow route reload to be prevented (<https://github.com/angular/angular.js/commit/2f0a50b526c5d0263879d3e845866e1af6fd9791|2f0a50b5>, <https://github.com/angular/angular.js/issues/9824|#9824>, <https://github.com/angular/angular.js/issues/13894|#13894>)'
    eq_(expected, convert_md_links(text))


def test_convert_images():
    text = 'This is an image: ![](https://img-fotki.yandex.ru/get/67890/13558447.f/0_bc68a_c79b90d2_L.png) right?'
    expected = 'This is an image: https://img-fotki.yandex.ru/get/67890/13558447.f/0_bc68a_c79b90d2_L.png right?'
    eq_(expected, convert_md_images(text))

    text = 'This is an image: ![with title](https://img-fotki.yandex.ru/get/67890/13558447.f/0_bc68a_c79b90d2_L.png) right?'
    expected = 'This is an image: https://img-fotki.yandex.ru/get/67890/13558447.f/0_bc68a_c79b90d2_L.png right?'
    eq_(expected, convert_md_images(text))


def test_convert_bolds():
    text =      '* **$parse:** Copy `inputs` for expressions with expensive checks'
    expected =  '* *$parse:* Copy `inputs` for expressions with expensive checks'
    eq_(expected, convert_md_bolds(text))

    text = '* **dateFilter, input:** fix Date parsing in IE/Edge when timezone offset'
    expected= '* *dateFilter, input:* fix Date parsing in IE/Edge when timezone offset'
    eq_(expected, convert_md_bolds(text))
