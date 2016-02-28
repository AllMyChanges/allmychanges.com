from nose.tools import eq_
from unittest import TestCase
from allmychanges.changelog_updater import update_changelog_from_raw_data3
from allmychanges.models import Changelog
from allmychanges.env import Environment
from allmychanges.tests.utils import create_user


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
