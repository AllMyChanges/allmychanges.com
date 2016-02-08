from nose.tools import eq_, assert_raises

from ..validators import URLValidator
from django.core.validators import ValidationError
from .utils import refresh


def test_url_validator():
    validate = URLValidator()
    eq_(None, validate('http://www.sbcl.org/news.html'))
    eq_(None, validate('git://gitorious.org/clbuild2/clbuild2.git'))
    eq_(None, validate('git@github.com:sass/sass.git'))

    eq_(None, validate('http://alfredapp.com/changelog/'))
    eq_(None, validate('https://bitmessage.org/wiki/Changelog'))
    eq_(None, validate('http://selenic.com/hg/'))

    assert_raises(ValidationError, validate, 'blah.html')
