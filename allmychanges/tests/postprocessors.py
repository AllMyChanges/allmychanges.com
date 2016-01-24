from nose.tools import eq_
from allmychanges.parsing.postprocessors import sed


def test_sed_postprocessor():
    p = sed(ur's/(.*?) minor (.*?)/\1 \2/')
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
