from nose.tools import eq_
from allmychanges.parsing.postprocessors import sed


def test_simple_postprocessor():
    p = sed(ur's/(.*?) minor (.*?)/\1 \2/')
    eq_('blah again', p('blah minor again'))


def test_comments():
    p = sed(ur"""
# replace one value with another
s/(.*?) minor (.*?)/\1 \2/
""")
    eq_('blah again', p('blah minor again'))


def test_sed_postprocessor_with_multiple_rules():
    p = sed(ur"""
    s/(.*?) minor (.*?)/\1 \2/
    s/v(\d+)/\1/
    """)
    eq_('blah 123', p('blah minor v123'))


def test_sed_multiline_matching():
    p = sed(ur's/^blah .*//')
    text = """
blah minor
and
blah again
    """
    expected = """

and

    """

    eq_(expected, p(text))


def test_make_rst_links():
    p = sed(ur's/GH#(?P<number>\d+)/`GH#\g<number> <https:\/\/github.com\/lxml\/lxml\/pull\/\g<number>>`_/')

    eq_('* `GH#187 <https://github.com/lxml/lxml/pull/187>`_: Now supports (only) version 5.x and later of PyPy.',
        p('* GH#187: Now supports (only) version 5.x and later of PyPy.'))
