# coding: utf-8
import datetime
import re

from nose.tools import eq_
from allmychanges.env import Environment
from allmychanges.parsing.pipeline import vcs_processing_pipe


def simplify(version):
    """Returns tuple of version-number, date, list-of-items."""
    return (version.version,
            version.date,
            [re.sub(ur'<span class="changelog-item-type.*?</span>',
                    u'',
                    item['text'])
             for item in version.content[0]])

def test_extract_from_vcs():
    date = datetime.date
    versions = vcs_processing_pipe([
        (None,    date(2014, 1, 15), 'Initial commit'),
        (None,    date(2014, 1, 15), 'Feature was added'),
        ('0.1.0', date(2014, 1, 16), 'Tests were added'),
        (None,    date(2014, 2, 9),  'Repackaging'), # such gaps should be considered
        # as having previous version
        ('0.2.0', date(2014, 2, 10), 'Some new functions'),
        ('0.2.0', date(2014, 2, 11), 'Other feature'),
        ('0.3.0', date(2014, 2, 14), 'Version bump'),
        ('0.3.0', date(2014, 3, 20), 'First unreleased feature'),
        ('0.3.0', date(2014, 3, 21), 'Second unreleased feature')])

    eq_([('x.x.x',
          None,
          ['First unreleased feature',
           'Second unreleased feature']),
         ('0.1.0',
          date(2014, 1, 16),
          ['Initial commit',
           'Feature was added',
           'Tests were added']),
         ('0.2.0',
          date(2014, 2, 10),
          ['Repackaging',
           'Some new functions']),
         ('0.3.0',
          date(2014, 2, 14),
          ['Other feature',
           'Version bump']),
     ], map(simplify, versions))


def test_ignore_vcs_versions_if_there_is_only_one_unreleased_version():
    date = datetime.date
    versions = vcs_processing_pipe(
        [(None, date(2014, 1, 15), 'Initial commit'),
         (None, date(2014, 1, 15), 'Feature was added'),
         (None, date(2014, 1, 16), 'Tests were added')])
    eq_([], versions)
