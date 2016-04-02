import types
import datetime

from nose.tools import eq_ as orig_eq_
from unittest import skip
from allmychanges.utils import first, html_document_fromstring
from allmychanges.parsing.pipeline import (
    get_markup,
    extract_metadata,
    group_by_path,
    strip_outer_tag,
    prerender_items,
    highlight_keywords,
    parse_plain_file,
    parse_markdown_file,
    filter_versions,
    parse_file)
from allmychanges.env import Environment


def eq_(left, right):
    if isinstance(left, types.GeneratorType):
        left = list(left)

    if isinstance(right, types.GeneratorType):
        right = list(right)
    orig_eq_(left, right, '\n{0}\n!=\n{1}'.format(repr(left), repr(right)))


def eq_dict(left, right):
    from dictdiffer import diff
    result = list(diff(left, right))
    if result:
        formatted = '\n' + '\n'.join(
            map(repr, result))
        raise AssertionError(formatted)


env = Environment(type='root', title='')
create_file = lambda filename, content: env.push(type='file_content',
                                                 filename=filename,
                                                 content=content)


def test_parsing_files():
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

    eq_("""<h1>Minor changes</h1>\n<p>This release has small importance.</p>
<ul>
<li>Test case was introduced</li>
</ul>
<p>Final word.</p>""",
        sc)


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

    # from https://github.com/celery/celery/blob/3.1/Changelog
    eq_('rst', get_markup('CHANGES',
                           "* [Security: `CELERYSA-0002`_] Insecure default umask."))

    eq_('rst', get_markup('CHANGES',
                           "- **Results**: ``result.get()`` was misbehaving."))

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

    # part of the sbcl's html changelog
    eq_('html', get_markup('Changelog', """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
    <html
    ><head
     >"""))


def test_extract_metadata():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    input_data = v(title='1.0 (2014-06-24)',
                   content='Fixed issue')

    eq_([v(type='prerender_items',
           title='1.0 (2014-06-24)',
           content='Fixed issue',
           date=datetime.date(2014, 6, 24))],
        extract_metadata(input_data))


def test_prerender_inserts_labels_into_content_items():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    input_data = v(type='prerender_items',
                   title='1.0 (2014-06-24)',
                   content='<p>Some bug was <em>fixed</em> issue</p>',
                   date=datetime.date(2014, 6, 24))
    expected = '<p>Some <span class="changelog-highlight-fix">bug</span> was <em><span class="changelog-highlight-fix">fixed</span></em> issue</p>'
    eq_(expected, first(prerender_items(input_data)).processed_content)

    input_data = v(type='prerender_items',
                   title='1.0 (2014-06-24)',
                   content='Fixed issue',
                   date=datetime.date(2014, 6, 24))
    expected = '<span class="changelog-highlight-fix">Fixed</span> issue'
    eq_(expected, first(prerender_items(input_data)).processed_content)


def test_keywords_highlighting():
    eq_('Some <span class="changelog-highlight-fix">breaking changes</span>',
        highlight_keywords('Some breaking changes'))
    eq_('Various <span class="changelog-highlight-fix">bugfixes</span>',
        highlight_keywords('Various bugfixes'))
    eq_('<span class="changelog-highlight-fix">Fixed a bug</span> where blah minor',
        highlight_keywords('Fixed a bug where blah minor'))
    eq_('<span class="changelog-highlight-fix">Bug Fixes</span>',
        highlight_keywords('Bug Fixes'))
    eq_('Some <span class="changelog-highlight-fix">bug</span> was <span class="changelog-highlight-fix">fixed</span>.',
        highlight_keywords('Some bug was fixed.'))
    eq_('<span class="changelog-highlight-fix">Fix</span> an issue.',
        highlight_keywords('Fix an issue.'))
    eq_('<span class="changelog-highlight-fix">Fixes</span> an issue.',
        highlight_keywords('Fixes an issue.'))
    eq_('This function is <span class="changelog-highlight-dep">deprecated</span>.',
        highlight_keywords('This function is deprecated.'))
    eq_('This is a <span class="changelog-highlight-fix">bugfix</span> release.',
        highlight_keywords('This is a bugfix release.'))

    # Backward
    eq_('This feature was <span class="changelog-highlight-inc">removed</span>.',
        highlight_keywords('This feature was removed.'))
    eq_('This change is <span class="changelog-highlight-inc">backward incompatible</span>.',
        highlight_keywords('This change is backward incompatible.'))

    # security
    eq_('Improved <span class="changelog-highlight-sec">XSS</span> filtering',
        highlight_keywords('Improved XSS filtering'))
    eq_('Improved <span class="changelog-highlight-sec">security</span> in SQL',
        highlight_keywords('Improved security in SQL'))

    # multiple
    eq_('attention to <span class="changelog-highlight-fix">bugfixes</span> and <span class="changelog-highlight-sec">security</span> issues',
        highlight_keywords('attention to bugfixes and security issues'))


def test_extract_metadata_is_able_to_detect_unreleased_version():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    eq_([v(type='prerender_items',
           title='1.0 (unreleased)',
           unreleased=True,
           content='')],
        extract_metadata(
            v(title='1.0 (unreleased)',
              content='')))

    eq_([v(type='prerender_items',
           title='1.45 (not yet released)',
           unreleased=True,
           content='')],
        extract_metadata(
            v(title='1.45 (not yet released)',
              content='')))

    eq_([v(type='prerender_items',
           title='1.45 (Under Development)',
           unreleased=True,
           content='')],
        extract_metadata(
            v(title='1.45 (Under Development)',
              content='')))

    eq_([v(type='prerender_items',
           title='1.45',
           unreleased=True,
           content='Under Development')],
        extract_metadata(
            v(title='1.45',
              content='Under Development')))


def test_extract_metadata_ignores_unreleased_keywords_if_date_was_found_ealier():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    expected = [v(type='prerender_items',
                  title='1.0 (2015-02-06)',
                  date=datetime.date(2015, 2, 6),
                  content='unreleased')]
    version = v(title='1.0 (2015-02-06)', content='unreleased')

    result = list(extract_metadata(version))

    eq_(expected, result)



def test_extract_date_only_from_first_three_lines():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    eq_(datetime.date(2015, 12, 14),
        first(extract_metadata(
            v(title='1.0',
              content='one\ntwo\n2015-12-14'))).date)

    eq_(None,
        getattr(first(extract_metadata(
            v(title='1.0',
              content='one\ntwo\nthree\n2015-12-14'))), 'date', None))


def test_extract_unreleased_keywords_only_from_first_three_lines():
    env = Environment()
    env.type = 'almost_version'
    v = lambda **kwargs: env.push(**kwargs)

    eq_(True,
        first(extract_metadata(
            v(title='1.0',
              content='one\ntwo\nunreleased'))).unreleased)

    eq_(None,
        getattr(first(extract_metadata(
            v(title='1.0',
              content='one\ntwo\nthree\nunreleased'))), 'unreleased', None))


def test_grouping_by_path():
    env = Environment()
    env.type = 'version'
    v = lambda filename: env.push(filename=filename)

    versions = [(10, v('docs/notes/0.1.0.rst')),
                (10, v('docs/notes/0.2.0.rst')),
                (10, v('docs/README')),
                (1000, v('CHANGES'))]

    eq_({'CHANGES': {'score': 1000, 'versions': [v('CHANGES')]},
         'docs/': {'score': 30 - 5, 'versions': [v('docs/notes/0.1.0.rst'),
                                                 v('docs/notes/0.2.0.rst'),
                                                 v('docs/README')]},
         'docs/README': {'score': 10, 'versions': [v('docs/README')]},
         'docs/notes/': {'score': 20 - 2, 'versions': [v('docs/notes/0.1.0.rst'),
                                                       v('docs/notes/0.2.0.rst')]},
         'docs/notes/0.1.0.rst': {'score': 10, 'versions': [v('docs/notes/0.1.0.rst')]},
         'docs/notes/0.2.0.rst': {'score': 10, 'versions': [v('docs/notes/0.2.0.rst')]}},

            group_by_path(versions))


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

    # also, it should remove several nested tags too
    eq_('Some text',
        strip_outer_tag('<li><p>Some text</p></li>'))

    # and it shouldn't stuck at such strange things
    eq_('Blah',
        strip_outer_tag('<p>Blah'))

    # but should leave as is if there isn't any common root node
    eq_('<p>Blah</p><p>minor</p>',
        strip_outer_tag('<p>Blah</p><p>minor</p>'))

    # and shouldn't broke on comment lines
    eq_('Blah',
        strip_outer_tag('<!--Comment-->Blah'))


def test_parse_plain_text():
    source = u"""
0.1:

 * Initial release

0.1.1

 * Added benchmarking script
 * Added support for more
   serializer modules"""

    _test_plain_parser(
        source,
        [
            u'<ul><li>Initial release</li></ul>',
            (u'<ul><li>Added benchmarking script</li>'
             u'<li>Added support for more<br/>serializer modules</li></ul>'),
            '<pre>' + source + '</pre>',
        ]
    )


def test_parse_redispy_style_plain_text():
    source = u"""
* 2.10.2
    * Added support for Hiredis's new bytearray support. Thanks
      https://github.com/tzickel
    * Fixed a bug when attempting to send large values to Redis in a Pipeline.
* 2.10.1
    * Fixed a bug where Sentinel connections to a server that's no longer a
      master and receives a READONLY error will disconnect and reconnect to
      the master."""

    _test_plain_parser(
        source,
        [
            (u'<ul><li>Added support for Hiredis\'s new bytearray support. Thanks<br/>https://github.com/tzickel</li>'
             '<li>Fixed a bug when attempting to send large values to Redis in a Pipeline.</li></ul>'),
            (u'<ul><li>Fixed a bug where Sentinel connections to a server that\'s no longer a<br/>master and receives a READONLY error will disconnect and reconnect to<br/>the master.</li></ul>'),
            '<pre>' + source + '</pre>'
        ])


def test_plaintext_parser_ignores_nested_versions():
    # this is a snippet from Node's changelog
    # https://raw.githubusercontent.com/joyent/node/master/ChangeLog
    file = create_file('Changes',
"""
2015.02.06, Version 0.12.0 (Stable)

* npm: Upgrade to 2.5.1

* mdb_v8: update for v0.12 (Dave Pacheco)
""")

    versions = list(parse_plain_file(file))
    eq_(2, len(versions))

    eq_('Changes', versions[1].title)

    v = versions[0]
    eq_('2015.02.06, Version 0.12.0 (Stable)', v.title)
    eq_('<ul><li>npm: Upgrade to 2.5.1</li></ul>\n<ul><li>mdb_v8: update for v0.12 (Dave Pacheco)</li></ul>',
        v.content)


def _test_parser(parser, given, expected):
    file = create_file('Changes', given)

    versions = list(parser(file))
    expected = [expected] if isinstance(expected, basestring) else expected
    assert len(versions) >= len(expected)

    for v, ex_v in zip(versions, expected):
        eq_(ex_v.strip(), v.content.strip())
    eq_(len(versions), len(expected))

_test_plain_parser = lambda *args: _test_parser(parse_plain_file, *args)
_test_md_parser = lambda *args: _test_parser(parse_markdown_file, *args)


def test_nodejs_parsing():
    source = u"""
2009.08.13, Version 0.1.4, 0f888ed6de153f68c17005211d7e0f960a5e34f3

      * Major refactor to evcom.

      * Upgrade v8 to 1.3.4
        Upgrade libev to 3.8
        Upgrade http_parser to v0.2
"""

    _test_plain_parser(
        source,
        [
            u"""
<ul><li>Major refactor to evcom.</li></ul>
<ul><li>Upgrade v8 to 1.3.4<br/>Upgrade libev to 3.8<br/>Upgrade http_parser to v0.2</li></ul>
            """,
            '<pre>' + source + '</pre>'
        ])


@skip('waiting for implementation')
def test_plaintext_parsing_of_nested_lists():
    source = u"""
2015.03.09 version 0.8.15
* First
  * Second
    * Third
      * Forth
      * Fifths
    * Six
      * Seven
      * Eight
"""

    _test_plain_parser(
        source,
        [
            u"""
<ul><li>First
        <ul><li>Second
                <ul><li>Third
                        <ul><li>Fourth</li>
                            <li>Fifths</li></ul></li>
                    <li>Six
                        <ul><li>Seven</li>
                            <li>Eight</li></ul></li></ul></li></ul></li></ul>
            """,
            '<pre>' + source + '</pre>'
        ]
    )


def test_versions_filter():
    fs = env.push(type='file_section')
    v1_0 = fs.push(version='1.0')
    fs1 = fs.push(type='file_section')
    v1_0_1 = fs1.push(version='1.0.1')
    fs2 = fs.push(type='file_section')
    v1_0_2 = fs2.push(version='1.0.2')

    versions = filter_versions([v1_0, v1_0_1, v1_0_2])
    eq_(2, len(versions))
    eq_(v1_0_1, versions[0])
    eq_(v1_0_2, versions[1])


def test_versions_filter2():
    fs = env.push(type='file_section')
    v1_0_5 = fs.push(type='version', version='1.0.5')
    fs_child = fs.push(type='file_section')
    v2_6 = fs_child.push(type='version', version='2.6')

    versions = filter_versions([v1_0_5, v2_6])
    eq_(1, len(versions))
    eq_(v1_0_5, versions[0])


def test_html_document_fromstring():
    doc = html_document_fromstring(u"""<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html>Blah</html>""")
    assert doc != None
