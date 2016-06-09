# coding: utf-8

import re

from nose.tools import eq_
from mock import patch
from allmychanges.models import (
    Changelog,
    FeedItem,
)
from .utils import create_user
from allmychanges.changelog_updater import (
    update_preview_or_changelog)
from allmychanges.management.commands.send_digests2 import (
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

    # there are two versions in this changelog: 0.1.0 and 0.1.1
    # we tag old version
    tagged_version = '0.1.0'
    tag = 'blah-minor'
    changelog.set_tag(art, tag, tagged_version)
    # and remove it from the user's feed to emulate
    # a case when 0.1.0 was in database, and only 0.1.1
    # was discovered during update
    FeedItem.objects.filter(user=art, version__number=tagged_version).delete()

    # also, we have a hanging tag for which there is no data in DB
    another_tag = 'foo'
    unknown_number = 'custom'
    changelog.set_tag(art, another_tag, unknown_number)

    with patch('allmychanges.notifications.email._send_email') as send_email:
        send_digest_to(art)
        # we send two emails one - to user and one to my email.
        eq_(2, send_email.call_count)
        body = send_email.call_args[0][0]

        tag_mention = (
            (
                ur'Tags: '
                ur'<a href="https://allmychanges.com'
                ur'/p/python/pip/#{0}"[^>]*>{0} \({1}\)</a>, '
                ur'<a href="https://allmychanges.com'
                ur'/p/python/pip/#{2}"[^>]*>{2} \({3}\)</a>'
            ).format(
                tag,
                tagged_version,
                another_tag,
                unknown_number,
            )
        )
        match = re.search(tag_mention, body)
        if match is None:
            filename = 'email-body.html'
            with open(filename, 'w') as f:
                f.write(body)
                message = ('Tags are not mentioned in the email body. '
                           'You will can inspect it opening file "{0}".').format(
                               filename)
                assert False, message
