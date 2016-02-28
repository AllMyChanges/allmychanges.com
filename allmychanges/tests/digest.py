# coding: utf-8

from nose.tools import eq_
from unittest import TestCase
from allmychanges.models import Changelog
from allmychanges.digest import (
    get_digest_for,
    mark_digest_sent_for)
from django.utils import timezone
from allmychanges.tests.utils import create_user
from hamcrest import (
    assert_that,
    has_entries,
    has_length,
    contains)


class DigestTests(TestCase):
    def setUp(self):
        self.changelog = Changelog.objects.create(
            namespace='python', name='pip', source='test')
        self.user = create_user('art')
        self.user.track(self.changelog)

        now = timezone.now()

        # we already know about one version
        for idx in range(1, 11):
            version = self.changelog.versions.create(
                number='0.{}.0'.format(idx),
                discovered_at=now)
            self.user.add_feed_item(version)

    def test_if_we_didn_have_a_mark_show_all(self):
        digest = get_digest_for(self.user)

        assert_that(digest,
                    contains(
                        has_entries(
                            name='pip',
                            versions=has_length(10))))

    def test_when_mark_is_saved_digest_returns_empty_list(self):
        mark_digest_sent_for(self.user)
        digest = get_digest_for(self.user)
        eq_(0, len(digest))
