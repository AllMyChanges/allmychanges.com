# coding: utf-8

from allmychanges.utils import html2md

from nose.tools import eq_

from allmychanges.notifications.slack import (
    convert_md_links,
    convert_md_bolds,
    convert_md_images,
)


def test_html2md_dont_break_links():
    # original html2text breaks long lines and links in them

    text = """<p>This release contains a variety of <span class="changelog-highlight-fix">fixes</span> from 9.5.1. For
  information about new features in the 9.5 major release, see
  <a href="http://www.postgresql.org/docs/devel/static/release-9-5.html">Section E.3</a>.</p>"""

    expected = u'This release contains a variety of fixes from 9.5.1. For information about new features in the 9.5 major release, see [Section E.3](http://www.postgresql.org/docs/devel/static/release-9-5.html).'

    result = html2md(text)
    eq_(expected, result.strip())


def test_html2md_dont_break_long_links2():
    text = """<div style="display: none;"></div><span>The beta channel has been updated to 50.0.2661.49 for Windows, Mac, and Linux.</span><span>A partial list of changes is available in the</span><a href="https://chromium.googlesource.com/chromium/src/+log/50.0.2661.37..50.0.2661.49?pretty=fuller&amp;n=10000"><span> </span><span>log</span></a><span>. Interested in</span><a href="http://www.chromium.org/getting-involved/dev-channel"><span> </span><span>switching</span></a><span> release channels? Find out</span><a href="http://www.chromium.org/getting-involved/dev-channel"><span> </span><span>how</span></a><span>. If you find a new issue, please let us know by</span><a href="http://crbug.com/"><span> </span><span>filing a <span class="changelog-highlight-fix">bug</span></span></a><span>. The</span><a href="https://productforums.google.com/forum/#!forum/chrome"><span> </span><span>community help forum</span></a><span> is also a great place to reach out for help or learn about common issues.</span>"""
    expected = u'The beta channel has been updated to 50.0.2661.49 for Windows, Mac, and Linux.A partial list of changes is available in the[ log](https://chromium.googlesource.com/chromium/src/+log/50.0.2661.37..50.0.2661.49?pretty=fuller&n=10000). Interested in[ switching](http://www.chromium.org/getting-involved/dev-channel) release channels? Find out[ how](http://www.chromium.org/getting-involved/dev-channel). If you find a new issue, please let us know by[ filing a bug](http://crbug.com/). The[ community help forum](https://productforums.google.com/forum/#!forum/chrome) is also a great place to reach out for help or learn about common issues.'


    result = html2md(text)
    eq_(expected, result.strip())


def test_convert_links():
    text = 'see [ some ](http://example.com).'
    expected = 'see <http://example.com| some >.'
    eq_(expected, convert_md_links(text))

    text = 'see [Section E.3](http://www.postgresql.org/docs/devel/static/release-9-5.html).'
    expected = 'see <http://www.postgresql.org/docs/devel/static/release-9-5.html|Section E.3>.'
    eq_(expected, convert_md_links(text))

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
