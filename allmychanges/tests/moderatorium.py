import anyjson
import datetime

from allmychanges.models import Changelog, LightModerator
from django.test import Client
from django.utils import timezone
from django.core.urlresolvers import reverse

from .utils import (create_user,
                    eq_,
                    check_status_code)


THEBOT_GITHUB_URL = 'http://github.com/svetlyak40wt/thebot'


def test_light_user_becomes_a_moderator_after_changing_changelog():
    changelog = Changelog.objects.create(
        namespace='python', name='thebot', source=THEBOT_GITHUB_URL)
    cl = Client()
    check_status_code(200,
                      cl.put(reverse('changelog-detail',
                                     kwargs=dict(pk=changelog.id)),
                             data=anyjson.serialize(dict(
                                 source=changelog.source,
                                 downloader='vcs.git')),
                             content_type='application/json'))
    eq_(1, changelog.light_moderators.count())

    # and second save don't add him again
    check_status_code(200,
                      cl.put(reverse('changelog-detail',
                                     kwargs=dict(pk=changelog.id)),
                             data=anyjson.serialize(dict(
                                 source=changelog.source,
                                 downloader='vcs.git')),
                            content_type='application/json'))
    eq_(1, changelog.light_moderators.count())


    # and another light user unable to change this changelog anymore
    another_cl = Client()
    check_status_code(403,
                      another_cl.put(reverse('changelog-detail',
                                             kwargs=dict(pk=changelog.id)),
                                     data=anyjson.serialize(dict(source=changelog.source)),
                                     content_type='application/json'))
    # and there is still only one moderator
    eq_(1, changelog.light_moderators.count())


def test_normal_user_becomes_a_moderator_after_changing_changelog():
    changelog = Changelog.objects.create(
        namespace='python', name='thebot', source=THEBOT_GITHUB_URL)
    create_user('art')
    cl = Client()
    cl.login(username='art', password='art')

    check_status_code(200,
                      cl.put(reverse('changelog-detail',
                                     kwargs=dict(pk=changelog.id)),
                             data=anyjson.serialize(dict(
                                 source=changelog.source,
                                 downloader='vcs.git')),
                             content_type='application/json'))
    eq_(0, changelog.light_moderators.count())
    eq_(1, changelog.moderators.count())

    # and second call dont add him again
    check_status_code(200,
                      cl.put(reverse('changelog-detail',
                                     kwargs=dict(pk=changelog.id)),
                             data=anyjson.serialize(dict(
                                 source=changelog.source,
                                 downloader='vcs.git')),
                             content_type='application/json'))
    eq_(0, changelog.light_moderators.count())
    eq_(1, changelog.moderators.count())

    # and another normal user is unable to change this changelog anymore
    create_user('vasya')
    another_cl = Client()
    another_cl.login(username='vasya', password='vasya')
    check_status_code(403,
                      another_cl.put(reverse('changelog-detail',
                                             kwargs=dict(pk=changelog.id)),
                                     data=anyjson.serialize(dict(source=changelog.source)),
                                     content_type='application/json'))
    # and there is still only one moderator
    eq_(0, changelog.light_moderators.count())
    eq_(1, changelog.moderators.count())


def test_merge_light_moderator():
    changelog = Changelog.objects.create(
        namespace='python', name='thebot', source=THEBOT_GITHUB_URL)
    changelog.light_moderators.create(light_user='12345')

    art = create_user('art')
    eq_(False, changelog.editable_by(art))

    LightModerator.merge(art, '12345')
    eq_(0, changelog.light_moderators.count())
    eq_(1, changelog.moderators.count())
    eq_(True, changelog.editable_by(art))


def test_light_moderators_removed_after_24_hours():
    changelog = Changelog.objects.create(
        namespace='python', name='thebot', source=THEBOT_GITHUB_URL)
    moderator = changelog.light_moderators.create(light_user='12345')
    moderator.created_at = timezone.now() - datetime.timedelta(1, 1)
    moderator.save()

    LightModerator.remove_stale_moderators()
    eq_(0, changelog.light_moderators.count())
