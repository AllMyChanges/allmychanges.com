# coding: utf-8

import datetime
import arrow

from django.utils import timezone
from nose.tools import eq_
from unittest import TestCase
from allmychanges.changelog_updater import update_changelog_from_raw_data3
from allmychanges.models import Changelog
from allmychanges.env import Environment
from allmychanges.tests.utils import create_user, dt_eq


def v(**kwargs):
    kwargs.setdefault('content', '')
    kwargs.setdefault('processed_content', '')
    env = Environment()
    env._data.update(kwargs)
    return env


class UpdaterTests(TestCase):
    def setUp(self):
        self.changelog = Changelog.objects.create(
            namespace='python', name='pip', source='test')
        self.user = create_user('art')
        self.user.track(self.changelog)

        # we already know about one version
        self.changelog.versions.create(number='0.2.0')

    def test_update_changelog_creates_feed_items_for_new_versions(self):
        # we discovered a new 0.3.0 version
        # and it should be added to user's feed
        data = [v(version='0.2.0'),
                v(version='0.3.0')]

        eq_(0, self.user.feed_versions.count())
        update_changelog_from_raw_data3(self.changelog, data)
        eq_(1, self.user.feed_versions.count())


    def test_feed_items_not_created_for_unreleased_version(self):
        # we discovered a new 0.3.0 version, but it is not released yet
        # and it should NOT be added to user's feed
        data = [v(version='0.2.0'),
                v(version='0.3.0', unreleased=True)]

        eq_(0, self.user.feed_versions.count())
        update_changelog_from_raw_data3(self.changelog, data)
        eq_(0, self.user.feed_versions.count())

    def test_feed_item_created_when_unreleased_version_become_released(self):
        # we already discovered 0.3.0 version, but it was unreleased
        self.changelog.versions.create(number='0.3.0', unreleased=True)

        # now we discovered it again, and it is released now!
        data = [v(version='0.2.0'),
                v(version='0.3.0')]

        eq_(0, self.user.feed_versions.count())
        update_changelog_from_raw_data3(self.changelog, data)
        eq_(1, self.user.feed_versions.count())

    def test_items_with_release_date_always_added_to_feed_if_not_older_than_month(self):
        now = timezone.now()
        d = datetime.timedelta
        data = [v(version='0.1.0', date=now - d(42)),
                v(version='0.1.1', date=now - d(21)),
                v(version='0.1.2', date=now - d(7)),
                v(version='0.1.3', date=now - d(1))]

        update_changelog_from_raw_data3(self.changelog, data)

        eq_(['0.1.3', '0.1.2', '0.1.1'],
            [ver.number for ver in self.user.feed_versions.all()])

    def test_when_release_date_unknown_add_all_tips_and_same_amount_of_their_parents_case1(self):
        self.changelog.versions.all().delete()

        data = [v(version='0.1.0'),
                v(version='0.1.1'),
                v(version='0.1.2'),
                v(version='0.1.3')]

        # in this case, 0.1.3 is the only one tip, and 0.1.2 it's parent
        # so, only they should be added to the feed

        update_changelog_from_raw_data3(self.changelog, data)

        eq_(['0.1.3', '0.1.2'],
            [ver.number for ver in self.user.feed_versions.all()])

    def test_when_release_date_unknown_add_all_tips_and_same_amount_of_their_parents_case2(self):
        self.changelog.versions.all().delete()

        data = [v(version='0.1.0'),
                v(version='0.1.1'),
                v(version='0.1.2'),
                v(version='0.2.0'),
                v(version='0.2.1')]

        # in this case, 0.1.2 and 0.2.1 are tips, and 0.1.1 with 0.2.0 are
        # their parents, only these version should be added to the feed
        # but not 0.1.0

        update_changelog_from_raw_data3(self.changelog, data)

        eq_(['0.2.1', '0.2.0', '0.1.2', '0.1.1'],
            [ver.number for ver in self.user.feed_versions.all()])


    def test_updater_sets_dicovered_at_in_now_if_it_is_none(self):
        self.changelog.versions.all().delete()

        special_date = arrow.get('2015-01-02').datetime

        data = [v(version='0.1.0'),
                v(version='0.1.1'),
                v(version='0.2.0', discovered_at=special_date),
                v(version='0.2.1')]

        update_changelog_from_raw_data3(self.changelog, data)

        # date should be changed only for 0.1.0, 0.1.1 and 0.2.1
        dates = {ver.number: ver.discovered_at
                 for ver in self.user.feed_versions.all()}

        now = timezone.now()
        dt_eq(now,          dates['0.1.0'])
        dt_eq(now,          dates['0.1.1'])
        dt_eq(special_date, dates['0.2.0'])
        dt_eq(now,          dates['0.2.1'])
