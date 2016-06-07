# coding: utf-8

import re

from nose.tools import eq_
from mock import patch
from allmychanges.models import Changelog
from .utils import create_user
from allmychanges.changelog_updater import (
    update_preview_or_changelog)
from allmychanges.management.commands.send_digests import (
    send_digest_to)


def test_email_with_changes_contains_tags():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/very-simple.md',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    version = changelog.versions.all()[0]
    tag = 'blah-minor'
    changelog.set_tag(art, tag, version.number)
    unknown_number = 'custom'
    changelog.set_tag(art, tag, unknown_number)

    with patch('allmychanges.notifications.email._send_email') as send_email:
        send_digest_to(art, period=7)
        # we send two emails one - to user and one to my email.
        eq_(2, send_email.call_count)
        body = send_email.call_args[0][0]
        tag_mention = (
            ur'Tags: '
            ur'<a href="https://allmychanges.com'
            ur'/p/python/pip/#{0}"[^>]*>{0} (</a>'.format(
            tag)
        )
        assert re.search(tag_mention, body) is not None
