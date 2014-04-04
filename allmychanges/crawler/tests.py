from datetime import date
from nose.tools import eq_

from . import (_filter_changelog_files, parse_changelog,
               _extract_version, _starts_with_ident, _parse_item,
               _extract_date,)
from allmychanges.utils import normalize_url, get_markup_type, get_commit_type


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
    eq_('1.0', parsed[0]['version'])
    eq_(date(2013, 12, 23), parsed[0]['date'])
    eq_('0.10.2', parsed[1]['version'])
    eq_('0.7.1', parsed[2]['version'])

    eq_(1, len(parsed[0]['sections']))
    eq_('(release date to be announced, codename to be selected)',
        parsed[0]['sections'][0]['notes'])

    eq_(1, len(parsed[0]['sections'][0]['items']))
    eq_(('Added ``SESSION_REFRESH_EACH_REQUEST`` config key that controls the '
         'set-cookie behavior.  If set to `True` a permanent session will be '
         'refreshed each request and get their lifetime extended, if set to '
         '`False` it will only be modified if the session actually modifies. '
         'Non permanent sessions are not affected by this and will always '
         'expire if the browser window closes.'),
        parsed[0]['sections'][0]['items'][0])


def test_preserve_newlines_in_long_notes():
    input = """
1.0
-----------

Some note with few paragraphs.
Each paragraph should be separated with empty line.

Like that.
"""
    parsed = parse_changelog(input)
    eq_("""Some note with few paragraphs. Each paragraph should be separated with empty line. 
Like that.""", parsed[0]['sections'][0]['notes'])
    

def test_extract_version():
    eq_(None, _extract_version('Just a text with some 1 33 nubers'))
    eq_('1.0', _extract_version('Version 1.0'))
    eq_('0.10.2', _extract_version('Version 0.10.2'))
    eq_('2.0.0', _extract_version('2.0.0 (2013-09-24)'))
    eq_(None, _extract_version('  some number in the item\'s text 0.1'))


def test_parse_item():
    eq_((False, 0, None), _parse_item('Blah minor'))
    eq_((False, 0, None), _parse_item('  Blah minor'))
    eq_((True, 2, 'Blah minor'), _parse_item('- Blah minor'))
    eq_((True, 3, 'Blah minor'), _parse_item(' - Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  -  Blah minor'))
    eq_((True, 5, 'Blah minor'), _parse_item('  *  Blah minor'))


def test_extract_date():
    eq_(None, _extract_date(''))
    eq_(None, _extract_date('ejwkjw kjjwk 20'))
    eq_(None, _extract_date('2009 thouth 15 fne 04'))
    eq_(None, _extract_date('11'))
    eq_(None, _extract_date('12.2009'))

    eq_(date(2009, 5, 23), _extract_date('2009-05-23'))
    eq_(date(2009, 5, 23), _extract_date('2009-5-23'))
    eq_(date(2009, 5, 3), _extract_date('2009-05-03'))
    eq_(date(2009, 5, 23), _extract_date('05-23-2009'))
    eq_(date(2009, 5, 23), _extract_date('05.23.2009'))
    eq_(date(2009, 5, 23), _extract_date('23.05.2009'))
    #eq_(date(2013, 3, 31), _extract_date('1.2.0 (2013-03-31)'))

    eq_(date(2009, 5, 23), _extract_date('(2009-05-23)'))
    eq_(date(2009, 5, 23), _extract_date('v 1.0.0 (2009-05-23)'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 2009-05-23 there were star wars'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 23-05-2009 there were star wars'))
    eq_(date(2009, 5, 23), _extract_date('in a far far 23.05.2009 there were star wars'))

    # could confuse day and month
    eq_(date(2009, 4, 5), _extract_date('04.05.2009'))


def test_starts_with_ident():
    eq_(False, _starts_with_ident('Blah', 0))
    eq_(False, _starts_with_ident('Blah', 1))
    eq_(False, _starts_with_ident(' Blah', 2))
    eq_(False, _starts_with_ident('  Blah', 1))
    eq_(True,  _starts_with_ident('  Blah', 2))
    eq_(True,  _starts_with_ident(' Blah', 1))


def test_url_normalization():
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('https://github.com/svetlyak40wt/blah'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('https://github.com/svetlyak40wt/blah/'))
    eq_(('git://github.com/svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('http://github.com/svetlyak40wt/blah'))
    eq_(('git@github.com:svetlyak40wt/blah', 'svetlyak40wt', 'blah'),
        normalize_url('git@github.com:svetlyak40wt/blah'))
    eq_(('https://some-server.com/repo', None, 'repo'),
        normalize_url('git+https://some-server.com/repo'))


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


def test_get_commit_type():
    eq_('new', get_commit_type('add new feature'))
    eq_('new', get_commit_type('new feature was added'))
    eq_('fix', get_commit_type('fix 100 bags'))
    eq_('fix', get_commit_type('100 bags were fixed'))
    eq_('fix', get_commit_type('change some bugfix'))
    eq_('fix', get_commit_type('some fixes'))
    eq_('fix', get_commit_type('[Fix] Resolved'))
    eq_('new', get_commit_type('change something'))
