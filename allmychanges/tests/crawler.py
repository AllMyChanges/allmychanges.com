from datetime import date
from nose.tools import eq_
from nose.plugins.attrib import attr

from allmychanges.crawler import (
    _filter_changelog_files,
    _extract_version, _parse_item,
    _extract_date)
from allmychanges.utils import get_markup_type, get_change_type
from allmychanges.downloaders.utils import normalize_url


def test_changelog_finder():
    in_ = [
          './release.sh',
          './HISTORY.rst',
          './docs/RELEASE_NOTES.TXT',
          './docs/releases.rst',
          './kiva/agg/freetype2/docs/release',
          './seed/commands/release.py',
          './doc/source/manual/AppReleaseNotes.rst',
          './src/robotide/application/releasenotes.py',
          './scripts/make-release.py',
          './pypi_release.sh',
          './doc/release.rst',
          './release-process.txt',
          './docs/release_notes/v0.9.15.rst',
          './release.sh',
          './.travis-release-requirements.txt',
          './mkrelease.sh',
          './README.rst',
    ]

    out = [
          './HISTORY.rst',
          './docs/RELEASE_NOTES.TXT',
          './docs/releases.rst',
          './doc/source/manual/AppReleaseNotes.rst',
          './doc/release.rst',
          './release-process.txt',
          './docs/release_notes/v0.9.15.rst',
          './.travis-release-requirements.txt',
          './README.rst',
    ]
    eq_(out, list(_filter_changelog_files(in_)))


def test_extract_version():
    def check(v, text=None):
        if text:
            eq_(v, _extract_version(text))
        else:
            eq_(v, _extract_version(v))
            eq_(v, _extract_version('v' + v))
            check(v, '{0} (2013-09-24)'.format(v))
            check(v, '{0} (2013.09.24)'.format(v))
            check(v, '**{0} (2014-05-16)**'.format(v))
            check(v, '**{0} (2014.05.16)**'.format(v))
            eq_(v, _extract_version('New version {0}'.format(v)))
            eq_(v, _extract_version('New version v{0}'.format(v)))
            eq_(v, _extract_version('2015-03-12 {0}'.format(v)))
            eq_(v, _extract_version('2015-03-12 v{0}'.format(v)))
            eq_(v, _extract_version('2015-03-12 ({0})'.format(v)))
            eq_(v, _extract_version('2015-03-12 (v{0})'.format(v)))

    # from https://app-updates.agilebits.com/product_history/OPI4
    check('5.3.BETA-22')

    # from http://spark.apache.org/releases/spark-release-1-3-0.html
    check(None, 'Upgrading to Spark 1.3')

    # https://archive.apache.org/dist/kafka/0.8.0/RELEASE_NOTES.html
    check('0.8.0', u'dist/kafka/0.8.0/RELEASE_NOTES.html')

    # https://github.com/numpy/numpy/tree/master/doc/release
    check('1.3.0', u'doc/release/1.3.0-notes.rst')

    # https://github.com/git/git/blob/master/Documentation/RelNotes/2.3.2.txt
    check(None, u'Fixes since v2.3.1')

    # this should work because we'll remove stop-words
    # like "release notes" and "for"
    check('3.0', u'Release Notes for MongoDB 3.0')

    # don't consider this a version
    # from https://bitbucket.org/cthedot/cssutils/src/d572ac8df6bd18cad203dea1bbf58867ff0d0ebe/docs/html/_sources/CHANGELOG.txt
    check(None, '0.3.x')

    # from https://github.com/meteor/meteor/blob/devel/History.md#v1032-2015-feb-25
    check('1.0.3.2', 'v.1.0.3.2, 2015-Feb-25')

    # from https://itunes.apple.com/ru/app/chrome-web-browser-by-google/id535886823?l=en&mt=8
    check('40.0.2214.73')
    check('05.10.2014.73')
    check('3.05.10.2014')
    # # from https://github.com/inliniac/suricata/blob/master/ChangeLog
    check('2.0.1rc1')
    check('2.0beta2')

    # from https://github.com/textmate/textmate/blob/master/Applications/TextMate/about/Changes.md
    check('2.0-beta.6.7', '2015-01-19 (v2.0-beta.6.7)')

    # # from https://github.com/ansible/ansible/blob/devel/CHANGELOG.md
    check('1.6.8', '1.6.8 "And the Cradle Will Rock" - Jul 22, 2014')

    check('0.2.1')
    # this horror is from the https://github.com/Test-More/TB2/blob/master/Changes
    check('1.005000_003')
    check('1.005000_003', '1.005000_003 Thu Mar 22 17:48:08 GMT 2012')

    check('3.0.0-pre', 'v3.0.0-pre (wip)')
    check('1.0.12')
    check('2.0.0-beta.1')

    check(None, 'Just a text with some 1 33 nubers')
    check('1.0')
    check('0.10.2')
    check('2.0.0')
    check('1.5.6')
    check('0.1.1', 'release-notes/0.1.1.md')
    check('1.3', 'doc/go1.3.html')
    check(None, '  some number in the item\'s text 0.1')
    check(None, 'This is the first version compatible with Django 1.7.')
    # this text is too long
    check(None, 'SWIG 3.0 required for programs that use SWIG library')
    check(None, 'HTTP/1.1 302 Found')
    check(None, '<script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>')


def test_parse_item():
    eq_((True, 0, 'Feature #1155: Log packet payloads in eve alerts'),
        _parse_item('Feature #1155: Log packet payloads in eve alerts'))

    eq_((False, 0, None),
        _parse_item('Some very long feature: doing blah'))

    eq_((False, 0, None), _parse_item('Blah minor'))
    eq_((False, 2, 'Blah minor'), _parse_item('  Blah minor'))
    eq_((True, 2, 'Blah minor'), _parse_item('- Blah minor'))
    eq_((True, 3, 'Blah minor'), _parse_item(' - Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  -  Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  *  Blah minor'))
    eq_((True, 5, 'Damn Nginx'), _parse_item('  *) Damn Nginx'))


def test_extract_date():
    # from https://github.com/lepture/mistune/blob/master/CHANGES.rst
    eq_(date(2014, 12, 5), _extract_date('Released on Dec. 5, 2014.'))

    eq_(date(2014, 10, 31), _extract_date('31/10/2014'))
    eq_(date(2013, 3, 13), _extract_date('13th March 2013'))
    eq_(date(2014, 11, 3), _extract_date('3rd November 2014'))
    eq_(date(2013, 2, 22), _extract_date('22nd Feb 2013'))

    eq_(None, _extract_date(''))
    eq_(None, _extract_date('ejwkjw kjjwk 20'))
    eq_(None, _extract_date('2009 thouth 15 fne 04'))
    eq_(None, _extract_date('11'))
    eq_(None, _extract_date('12.2009'))
    eq_(None, _extract_date('4.2-3252'))
    eq_(None, _extract_date('2009-05/23'))


    # https://github.com/lodash/lodash/wiki/Changelog#aug-17-2012--diff--docs
    eq_(date(2012, 8, 17), _extract_date('Aug. 17, 2012'))
    eq_(date(2009, 5, 23), _extract_date('2009-05-23'))
    eq_(date(2009, 5, 23), _extract_date('2009-5-23'))
    eq_(date(2009, 5, 3), _extract_date('2009-05-03'))
    eq_(date(2014, 5, 17), _extract_date('2014/05/17'))
    eq_(date(2009, 5, 23), _extract_date('05-23-2009'))
    eq_(date(2009, 5, 23), _extract_date('05.23.2009'))
    eq_(date(2009, 5, 23), _extract_date('23.05.2009'))
    eq_(date(2013, 3, 31), _extract_date('1.2.0 (2013-03-31)'))

    eq_(date(2009, 5, 23), _extract_date('(2009-05-23)'))
    eq_(date(2009, 5, 23), _extract_date('v 1.0.0 (2009-05-23)'))
    eq_(date(2014, 5, 16), _extract_date('**1.5.6 (2014-05-16)**'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 2009-05-23 there were star wars'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 23-05-2009 there were star wars'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 23.05.2009 there were star wars'))

    # this variant is from Nginx's changelog
    eq_(date(2014, 4, 24), _extract_date('   24 Apr 2014'))
    eq_(date(2014, 4, 28), _extract_date('April 28, 2014')) # from django

    # these two are from python's click
    eq_(date(2014, 5, 23), _extract_date('(bugfix release, released on May 23rd 2014)'))
    eq_(date(2014, 5, 21), _extract_date('(no codename, released on May 21st 2014)'))
    eq_(date(2014, 8, 13), _extract_date('August 13th 2014'))

    # like click's but from handlebars.js
    eq_(date(2014, 9, 1), _extract_date('September 1st, 2014'))
    # and this one from https://enterprise.github.com/releases
    eq_(date(2012, 2, 9), _extract_date('February  9, 2012'))
    eq_(date(2014, 9, 2), _extract_date('September  2, 2014'))



    # from https://github.com/ingydotnet/boolean-pm/blob/master/Changes
    # https://github.com/miyagawa/Perlbal-Plugin-PSGI/blob/master/Changes
    eq_(date(2014, 8, 8), _extract_date('Fri Aug  8 19:12:51 PDT 2014'))

    # from https://github.com/tadam/Test-Mock-LWP-Dispatch/blob/master/Changes
    eq_(date(2013, 5, 28), _extract_date('Tue May 28, 2013'))
    eq_(date(2013, 4, 1),  _extract_date('Mon Apr 01, 2013'))
    eq_(date(2013, 3, 29), _extract_date('Fri Mar 29, 2013'))

    # from https://github.com/alex/django-taggit/blob/develop/CHANGELOG.txt
    # we consider that first number is a month
    # all dates which use day in first position, should be normalized
    # by sed expressions
    eq_(date(2014, 10, 8), _extract_date('10.08.2014'))


def test_url_normalization():
    eq_(('https://github.com/lodash/lodash/wiki/Changelog', None, None),
        normalize_url('https://github.com/lodash/lodash/wiki/Changelog'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('https://github.com/svetlyak40wt/blah'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('https://github.com/svetlyak40wt/blah/'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('https://github.com/svetlyak40wt/blah.git'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('http://github.com/svetlyak40wt/blah'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('git@github.com:svetlyak40wt/blah.git'))
    eq_(('https://some-server.com/repo', None, 'repo'),
        normalize_url('git+https://some-server.com/repo'))
    eq_(('https://github.com/sass/sass', 'sass', 'sass'),
        normalize_url('git@github.com:sass/sass.git', for_checkout=False))
    eq_(('https://github.com/sass/sass', 'sass', 'sass'),
        normalize_url('https://github.com/sass/sass/releases', for_checkout=False))


def test_get_markup_type():
    eq_('markdown', get_markup_type('README.MD'))
    eq_('markdown', get_markup_type('README.md'))
    eq_('markdown', get_markup_type('readme.mD'))
    eq_('markdown', get_markup_type('readme.txt.md'))
    eq_('markdown', get_markup_type('readme.markdown'))
    eq_('markdown', get_markup_type('readme.MARKDOWN'))
    eq_('markdown', get_markup_type('readme.mdown'))

    eq_('rest', get_markup_type('README.RST'))
    eq_('rest', get_markup_type('README.rst'))
    eq_('rest', get_markup_type('README.rSt'))
    eq_('rest', get_markup_type('readme.txt.rst'))

    eq_(None, get_markup_type('README'))
    eq_(None, get_markup_type('readme.rd'))
    eq_(None, get_markup_type('readme.txt'))
    eq_(None, get_markup_type('readme.rst.'))


def test_get_change_type():
    eq_('new', get_change_type('add new feature'))
    eq_('new', get_change_type('new feature was added'))
    eq_('fix', get_change_type('fix 100 bags'))
    eq_('fix', get_change_type('100 bags were fixed'))
    eq_('fix', get_change_type('change some bugfix'))
    eq_('fix', get_change_type('some fixes'))
    eq_('fix', get_change_type('[Fix] Resolved'))
    eq_('new', get_change_type('change something'))
    eq_('sec', get_change_type('This issue solves CVE-2014-3556 report'))
    eq_('dep', get_change_type('pip install --build and pip install --no-clean are now deprecated'))
    eq_('inc', get_change_type('BACKWARD INCOMPATIBLE Removed the bundle support which was deprecated in 1.4.'))
    eq_('fix', get_change_type('bug fix: HANDLER-{BIND,CASE} no longer drop into ldb when a clause'))
    eq_('fix', get_change_type('BUG/MINOR: http: fix typos in previous patch'))
