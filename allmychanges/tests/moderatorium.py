import anyjson
import datetime

from mock import patch
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


def test_everybody_can_become_a_moderator():
    # right now I don't want to limit users abilitites to edit
    # projects and to fix parsing problems
    changelog = Changelog.objects.create(
        namespace='python',
        name='thebot',
        source=THEBOT_GITHUB_URL,
    )

    create_user('art')
    cl = Client()
    cl.login(username='art', password='art')

    # before call there is no moderators
    eq_(0, changelog.moderators.count())

    check_status_code(
        200,
        cl.post(reverse('changelog-detail',
                        kwargs=dict(pk=changelog.id)) \
                + 'add_to_moderators/'))

    # after the call, user was added to moderators list
    eq_(1, changelog.moderators.count())
    assert 'art' in [u.username for u in changelog.moderators.all()]


def test_moderator_can_give_away_the_project():
    # Project moderator can give away his
    # administration rights on some project

    changelog = Changelog.objects.create(
        namespace='python',
        name='thebot',
        source=THEBOT_GITHUB_URL,
    )

    art = create_user('art')
    changelog.add_to_moderators(art)

    cl = Client()
    cl.login(username='art', password='art')

    # before call he is a moderator
    eq_(True, changelog.is_moderator(art))

    check_status_code(
        200,
        cl.post(reverse('changelog-detail',
                        kwargs=dict(pk=changelog.id)) \
                + 'remove_from_moderators/'))

    # after the call, user was removed to moderators list
    eq_(False, changelog.is_moderator(art))


def test_moderator_receives_email_on_new_issues():
    with patch('allmychanges.models.send_email') as send_email:
        changelog = Changelog.objects.create(
            namespace='python',
            name='thebot',
            source=THEBOT_GITHUB_URL,
        )

        create_user('bob')
        art = create_user('art')
        # only art is a moderator
        changelog.add_to_moderators(art)

        issue = changelog.issues.create(
            type='auto_paused',
            comment='Some shit happened',
        )
        send_email.assert_called_once_with(
            'art@example.yandex.ru',
            'New issue was filed for python/thebot',
            'new-issue.html',
            context={'issue': issue},
            tags=['allmychanges', 'new-issue'],
        )
