from datetime import date
from nose.tools import eq_

from allmychanges.crawler import (
    _filter_changelog_files, parse_changelog,
    _extract_version, _starts_with_ident, _parse_item,
    _extract_date)
from allmychanges.utils import get_markup_type, get_change_type
from allmychanges.downloader import normalize_url


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


def test_flask_parser():
    input = """
Flask Changelog
===============

Here you can see the full list of changes between each Flask release.

Version 1.0 (23-12-2013)
-----------

(release date to be announced, codename to be selected)

- Added ``SESSION_REFRESH_EACH_REQUEST`` config key that controls the
  set-cookie behavior.  If set to `True` a permanent session will be
  refreshed each request and get their lifetime extended, if set to
  `False` it will only be modified if the session actually modifies.
  Non permanent sessions are not affected by this and will always
  expire if the browser window closes.

Version 0.10.2
--------------

(bugfix release, release date to be announced)

- Fixed broken `test_appcontext_signals()` test case.
- Raise an :exc:`AttributeError` in :func:`flask.helpers.find_package` with a
  useful message explaining why it is raised when a PEP 302 import hook is used
  without an `is_package()` method.

Version 0.7.1
-------------

Bugfix release, released on June 29th 2011

- Added missing future import that broke 2.5 compatibility.
- Fixed an infinite redirect issue with blueprints.
"""
    parsed = parse_changelog(input)
    eq_(3, len(parsed))
    eq_('1.0', parsed[2]['version'])
    eq_(date(2013, 12, 23), parsed[2]['date'])
    eq_('0.10.2', parsed[1]['version'])
    eq_('0.7.1', parsed[0]['version'])

    eq_(1, len(parsed[2]['sections']))
    eq_('(release date to be announced, codename to be selected)',
        parsed[2]['sections'][0]['notes'])

    eq_(1, len(parsed[2]['sections'][0]['items']))
    eq_(('Added ``SESSION_REFRESH_EACH_REQUEST`` config key that controls the '
         'set-cookie behavior.  If set to `True` a permanent session will be '
         'refreshed each request and get their lifetime extended, if set to '
         '`False` it will only be modified if the session actually modifies. '
         'Non permanent sessions are not affected by this and will always '
         'expire if the browser window closes.'),
        parsed[2]['sections'][0]['items'][0])


def test_preserve_newlines_in_long_notes():
    input = """
1.0
-----------

Some note with few paragraphs.
Each paragraph should be separated with empty line.

Like that.
"""
    parsed = parse_changelog(input)
    eq_("""Some note with few paragraphs. Each paragraph should be separated with empty line. \nLike that.""", parsed[0]['sections'][0]['notes'])


def test_use_date_even_from_next_string():
    input = """
Version 1.1
-----------

(bugfix release, released on May 23rd 2014)

- fixed a bug that caused text files on Python 2 to not accept
  native strings.

Version 1.0
-----------

(no codename, released on May 21st 2014)

- Initial release.
"""
    parsed = parse_changelog(input)
    eq_(2, len(parsed))
    eq_('1.0', parsed[0]['version'])
    eq_(date(2014, 5, 21), parsed[0]['date'])

    eq_('1.1', parsed[1]['version'])
    eq_(date(2014, 5, 23), parsed[1]['date'])


def test_detect_unreleased_version_in_version_line():
    parsed = parse_changelog("""
1.0 (unreleased)
-----------

Some note.
""")
    eq_(True, parsed[0].get('unreleased'))


def test_detect_unreleased_version_but_not_in_notes():
    parsed = parse_changelog("""
Version 1.0
-----------

Change in a way how unreleased notes are parsed.
""")
    eq_(None, parsed[0].get('unreleased'))



def test_extract_version():
    # from https://github.com/ansible/ansible/blob/devel/CHANGELOG.md
    eq_('1.6.8', _extract_version('1.6.8 "And the Cradle Will Rock" - Jul 22, 2014'))

    eq_('0.2.1', _extract_version('2014-09-11 v0.2.1'))
    # this horror is from the https://github.com/Test-More/TB2/blob/master/Changes
    eq_('1.005000_003', _extract_version('1.005000_003'))
    eq_('1.005000_003', _extract_version('1.005000_003 Thu Mar 22 17:48:08 GMT 2012'))

    eq_('3.0.0-pre', _extract_version('v3.0.0-pre (wip)'))
    eq_('1.0.12', _extract_version('v1.0.12'))
    eq_('2.0.0-beta.1', _extract_version('2.0.0-beta.1'))
    eq_('2.0.0-beta.1', _extract_version('v2.0.0-beta.1'))

    eq_(None, _extract_version('Just a text with some 1 33 nubers'))
    eq_('1.0', _extract_version('Version 1.0'))
    eq_('0.10.2', _extract_version('Version 0.10.2'))
    eq_('2.0.0', _extract_version('2.0.0 (2013-09-24)'))
    eq_('1.5.6', _extract_version('**1.5.6 (2014-05-16)**'))
    eq_('0.1.1', _extract_version('release-notes/0.1.1.md'))
    eq_('1.3', _extract_version('doc/go1.3.html'))
    eq_(None, _extract_version('  some number in the item\'s text 0.1'))
    eq_(None, _extract_version('This is the first version compatible with Django 1.7.'))
    eq_(None, _extract_version('SWIG 3.0 required for programs that use SWIG'))
    eq_(None, _extract_version('HTTP/1.1 302 Found'))
    eq_(None, _extract_version('<script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>'))


def test_parse_item():
    eq_((False, 0, None), _parse_item('Blah minor'))
    eq_((False, 2, 'Blah minor'), _parse_item('  Blah minor'))
    eq_((True, 2, 'Blah minor'), _parse_item('- Blah minor'))
    eq_((True, 3, 'Blah minor'), _parse_item(' - Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  -  Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  *  Blah minor'))
    eq_((True, 5, 'Damn Nginx'), _parse_item('  *) Damn Nginx'))


def test_extract_date():
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
    eq_(date(2014, 8, 10), _extract_date('10.08.2014'))


def test_starts_with_ident():
    eq_(False, _starts_with_ident('Blah', 0))
    eq_(False, _starts_with_ident('Blah', 1))
    eq_(False, _starts_with_ident(' Blah', 2))
    eq_(False, _starts_with_ident('  Blah', 1))
    eq_(True,  _starts_with_ident('  Blah', 2))
    eq_(True,  _starts_with_ident(' Blah', 1))


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
