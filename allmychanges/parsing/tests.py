import types
import datetime

from nose.tools import eq_ as orig_eq_
from allmychanges.parsing.pipeline import (
    create_section,
    parse_changelog,
    filter_versions,
    get_markup,
    extract_metadata,
    group_by_path,
    strip_outer_tag,
    parse_file)
from allmychanges.parsing.raw import RawChangelog
from allmychanges.env import Environment


def eq_(left, right):
    if isinstance(left, types.GeneratorType):
        left = list(left)

    if isinstance(right, types.GeneratorType):
        right = list(right)
    orig_eq_(left, right)


class TestRawChangelog(RawChangelog):
    def __init__(self, fixture):
        self.fixture = fixture

    def get_chunks(self):
        for item in self.fixture:
            yield self.create_chunk(title=item['filename'],
                                    content=item['content'])


def test_simple():
    fixture = [
        dict(filename='CHANGELOG.md',
             content=
"""The lib
=======

0.3.1
-----

Small fixes.

0.3.0
-----

* Feature 1.
* Bugfix 2.

0.2.1
-----

* Unittests were added.
""")] 
    raw_changelog = TestRawChangelog(fixture)
    parsed = parse_changelog(raw_changelog)
    eq_(3, len(parsed))


def test_release_notes():
    fixture = [
        dict(filename='release-notes/0.1.0.md',
             content=
"""
Initial release
===============

I wrote this library as a proof of the concept.
"""),
        dict(filename='release-notes/0.1.1.md',
             content=
"""
Minor changes
===============

This release has small importance.

* Test case was introduced
""")] 
    raw_changelog = TestRawChangelog(fixture)
    parsed = parse_changelog(raw_changelog)
    eq_(2, len(parsed))


def test_parsing_files():
    env = Environment()
    create_file = lambda filename, content: env.push(type='file_content',
                                                     filename=filename,
                                                     content=content)
    files = [
        create_file('release-notes/0.1.0.md',
"""
Initial release
===============

I wrote this library as a proof of the concept.
"""),
        create_file('release-notes/0.1.1.md',
"""
Minor changes
===============

This release has small importance.

* Test case was introduced

Final word.
""")]
    versions = list(parse_file(files[0])) + list(parse_file(files[1]))
    eq_(4, len(versions))
    v1, v2, v3, v4 = versions
    eq_('release-notes/0.1.0.md', v1.title)
    eq_('Initial release', v2.title)
    eq_('release-notes/0.1.1.md', v3.title)
    eq_('Minor changes', v4.title)

    sc = v3.content

    eq_(3, len(sc))
    eq_("<h1>Minor changes</h1>\n\n<p>This release has small importance.</p>",
        sc[0])
    eq_(["Test case was introduced"],
        sc[1])
    eq_("<p>Final word.</p>",
        sc[2])


def test_markup_guesser_from_extension():
    eq_('markdown', get_markup('release-notes/0.1.1.md',
                               "Minor changes"))
    eq_('rst', get_markup('release-notes/0.1.1.rst',
                          "Minor changes"))
    eq_('plain', get_markup('release-notes/Changes',
                          "Minor changes"))


def test_markup_guesser_from_content():
    eq_('rst', get_markup('CHANGES',
                           "Some text with :func:`foo` mentioned."))

    eq_('markdown', get_markup('CHANGES',
                               """Some header
=========="""))

    eq_('markdown', get_markup('CHANGES',
                               """Some header
--------"""))

    eq_('markdown', get_markup('CHANGES',
                               "## Some 2 level header"))

    eq_('markdown', get_markup('CHANGES',
                               "Some [link](blah)"))
    
    eq_('markdown', get_markup('CHANGES',
                               "Some [link][blah]"))

    # but
    eq_('plain', get_markup('CHANGES',
                            "Some [thing] in brackets"))


    eq_('plain', get_markup('CHANGES',
"""
0.1:

 * Initial release

0.1.1

 * Added benchmarking script
 * Added support for more serializer modules"""))


def test_filter_versions():
    input_data = [
        create_section('0.1.0'),
        create_section('Just a header'),
        create_section('Version 3.1.5')]
    eq_([create_section('0.1.0', [], version='0.1.0'),
         create_section('Version 3.1.5', version='3.1.5')],
        list(filter_versions(input_data)))


def test_extract_metadata():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    input_data = v(title='1.0 (2014-06-24)',
                   content=[['Fixed issue']])

    eq_([v(type='prerender_items',
           title='1.0 (2014-06-24)',
           content=[[{'type': 'fix',
                      'text': 'Fixed issue'}]],
           date=datetime.date(2014, 6, 24))],
        extract_metadata(input_data))


def test_extract_metadata_is_able_to_detect_unreleased_version():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    eq_([v(type='prerender_items',
           title='1.0 (unreleased)',
           unreleased=True,
           content=[])],
        extract_metadata(
            v(title='1.0 (unreleased)',
              content=[])))

    eq_([v(type='prerender_items',
           title='1.45 (not yet released)',
           unreleased=True,
           content=[])],
        extract_metadata(
            v(title='1.45 (not yet released)',
              content=[])))


    
def test_grouping_by_path():
    env = Environment()
    env.type = 'version'
    v = lambda filename: env.push(filename=filename)

    eq_({'CHANGES': [v('CHANGES')],
         'docs/': [v('docs/notes/0.1.0.rst'),
                   v('docs/notes/0.2.0.rst'),
                   v('docs/README')],
         'docs/README': [v('docs/README')],
         'docs/notes/': [v('docs/notes/0.1.0.rst'),
                         v('docs/notes/0.2.0.rst')],
         'docs/notes/0.1.0.rst': [v('docs/notes/0.1.0.rst')],
         'docs/notes/0.2.0.rst': [v('docs/notes/0.2.0.rst')]},

        group_by_path([v('docs/notes/0.1.0.rst'),
                       v('docs/notes/0.2.0.rst'),
                       v('docs/README'),
                       v('CHANGES')]))


def test_strip_outer_tag():
    # simple case
    eq_('Added new feature.',
        strip_outer_tag('<li>Added new feature.</li>'))

    # a case with embedded html
    eq_('Added <b>new</b> feature.',
        strip_outer_tag('<li>Added <b>new</b> feature.</li>'))

    # a case with newline
    eq_('Added new\n feature.',
        strip_outer_tag('<li>Added new\n feature.</li>'))

    
    
    # and now multiline with embedded HTML
    eq_('Added new output <code>twiggy_goodies.logstash.LogstashOutput</code> which\nsends json encoded data via UDP to a logstash server.',
        strip_outer_tag('<li>Added new output <code>twiggy_goodies.logstash.LogstashOutput</code> which\nsends json encoded data via UDP to a logstash server.</li>'))


def test_parse_plain_text():
    env = Environment()
    create_file = lambda filename, content: env.push(type='file_content',
                                                     filename=filename,
                                                     content=content)
    file = create_file('Changes',
"""
0.1:

 * Initial release

0.1.1

 * Added benchmarking script
 * Added support for more
   serializer modules""")
    
    versions = list(parse_file(file))
    eq_(2, len(versions))
    v1, v2 = versions

    eq_('0.1:', v1.title)
    eq_('0.1.1', v2.title)

    eq_([["Initial release"]],
        v1.content)

    eq_([["Added benchmarking script",
          "Added support for more\nserializer modules"]],
        v2.content)


def test_parse_redispy_style_plain_text():
    env = Environment()
    create_file = lambda filename, content: env.push(type='file_content',
                                                     filename=filename,
                                                     content=content)
    file = create_file('Changes',
"""* 2.10.2
    * Added support for Hiredis's new bytearray support. Thanks
      https://github.com/tzickel
    * Fixed a bug when attempting to send large values to Redis in a Pipeline.
* 2.10.1
    * Fixed a bug where Sentinel connections to a server that's no longer a
      master and receives a READONLY error will disconnect and reconnect to
      the master.""")
    
    versions = list(parse_file(file))

    eq_(2, len(versions))
    v1, v2 = versions

    eq_('* 2.10.2', v1.title)
    eq_('* 2.10.1', v2.title)

    eq_([['Added support for Hiredis\'s new bytearray support. Thanks\nhttps://github.com/tzickel',
          'Fixed a bug when attempting to send large values to Redis in a Pipeline.']],
        v1.content)

    eq_([['Fixed a bug where Sentinel connections to a server that\'s no longer a\nmaster and receives a READONLY error will disconnect and reconnect to\nthe master.']],
        v2.content)


