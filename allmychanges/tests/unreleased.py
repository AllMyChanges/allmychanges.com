from nose.tools import eq_
from allmychanges.parsing.unreleased import mention_unreleased


def test_unreleased():
    eq_(True, mention_unreleased('release date and codename to be decided'))
    eq_(True, mention_unreleased('(not released yet)'))
    eq_(True, mention_unreleased('(In-Progress)'))
    eq_(True, mention_unreleased('Work in progress'))
    eq_(True, mention_unreleased('work in progress'))
    eq_(True, mention_unreleased('in development'))
    eq_(True, mention_unreleased('upcoming'))
    eq_(True, mention_unreleased('no release date'))
