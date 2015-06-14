from nose.tools import eq_
from allmychanges.parsing.unreleased import mention_unreleased


def test_unreleased():
    eq_(True, mention_unreleased('release date and codename to be decided'))
    eq_(True, mention_unreleased('(not released yet)'))
