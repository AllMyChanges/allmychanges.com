# coding: utf-8
import anyjson
import mock
import time

from nose.tools import eq_
from django.test import Client, TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse

from allmychanges.models import Changelog, Issue, UserHistoryLog
from allmychanges import chat
from .utils import check_status_code, create_user, put_json, post_json, json

# схема урлов
# / - список доступных урлов
# /digest/
# /packages/
# /package/:namespace/:name/


def setup():
    Changelog.objects.all().delete()


def test_show_packages():
    cl = Client()

    user = create_user('art')
    changelog = Changelog.objects.create(namespace='python',
                                         name='pip',
                                         source='https://github.com/pypa/pip',
                                         created_at=timezone.now())
    user.track(changelog)

    user = create_user('gena')
    changelog = Changelog.objects.create(namespace='python',
                                                  name='rest',
                                                  source='https://github.com/frame/work',
                                                  created_at=timezone.now())
    user.track(changelog)

    # user art could be able to see only his own packages
    cl.login(username='art', password='art')
    response = cl.get('/v1/changelogs/?tracked=True')
    eq_(200, response.status_code)
    data = anyjson.deserialize(response.content)
    eq_(1, len(data))
    eq_('pip', data[0]['name'])


def test_add_package():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')
    eq_(0, Changelog.objects.count())

    post_json(
        cl,
        '/v1/changelogs/',
        expected_code=201,
        namespace='python',
        name='pip',
        source='https://github.com/pypa/pip',
        downloader='vcs.git')
    eq_(1, Changelog.objects.count())


def test_put_does_not_affect_created_at_field():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')

    changelog = Changelog.objects.create(namespace='python',
                                       name='pip',
                                       source='https://github.com/some/url')
    created_at = Changelog.objects.get(pk=changelog.pk).created_at

    time.sleep(1)
    put_json(
        cl,
        '/v1/changelogs/{0}/'.format(changelog.id),
        expected_code=200,
        namespace='python',
        name='pip',
        source='https://github.com/pypa/pip',
        downloader='vcs.git')

    eq_(created_at, Changelog.objects.get(pk=changelog.pk).created_at)


def test_downloader_is_required_when_updating_changelog():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')

    source = 'https://github.com/pip/pip'
    changelog = Changelog.objects.create(namespace='python',
                                         name='pip',
                                         source=source)
    changelog.downloader = 'git'
    changelog.save()

    # first try not changing source
    put_json(
        cl,
        '/v1/changelogs/{0}/'.format(changelog.id),
        expected_code=400,
        namespace='python',
        name='pip',
        source=source)
    eq_('git', Changelog.objects.get(pk=changelog.pk).downloader)


class TransactionTests(TestCase):
#    use_transaction_isolation = False

    def tests_transactional_api_methods(self):
        """Check that API method is transactional and will leave
        database consistent if will broke in the middle"""

        cl = Client()

        create_user('art')
        cl.login(username='art', password='art')
        eq_(0, Changelog.objects.count())


        with mock.patch.object(Changelog.objects, 'get_queryset') as get_queryset:
            get_queryset.side_effect = RuntimeError
            try:
                post_json(
                    cl,
                    '/v1/changelogs/',
                    namespace='python',
                    name='pip',
                    source='https://github.com/pypa/pip')
            except RuntimeError:
                pass

        eq_(0, Changelog.objects.count())



def test_authenticated_user_track_changelog():
    cl = Client()

    user = create_user('art')
    cl.login(username='art', password='art')

    changelog = Changelog.objects.create(source='http://github.com/svetlyak40wt/thebot')

    eq_(1, Changelog.objects.count())
    eq_(0, user.changelogs.count())

    data = post_json(
        cl,
        '/v1/changelogs/{0}/track/'.format(changelog.id),
        expected_code=200)

    eq_({'result': 'ok'}, data)

    eq_(1, user.changelogs.count())


def test_when_anonymous_tracks_changelog_its_id_is_saved_into_the_cookie():
    cl = Client()
    changelog = Changelog.objects.create(source='http://github.com/svetlyak40wt/thebot')
    changelog2 = Changelog.objects.create(source='http://github.com/svetlyak40wt/django-fields')

    response = cl.post(reverse('changelog-track', kwargs=dict(pk=changelog.id)))
    eq_(200, response.status_code, response.content)
    eq_('{}'.format(changelog.pk),
        response.cookies['tracked-changelogs'].value)

    response = cl.post(reverse('changelog-track', kwargs=dict(pk=changelog2.id)))
    eq_('{},{}'.format(changelog.pk, changelog2.pk),
        response.cookies['tracked-changelogs'].value)


def test_if_after_login_will_track_changelogs_from_cookie():
    cl = Client()
    changelog = Changelog.objects.create(source='http://github.com/svetlyak40wt/thebot')

    post_json(
        cl,
        reverse('changelog-track', kwargs=dict(pk=changelog.id)),
        expected_code=200)

    user = create_user('art')
    cl.login(username='art', password='art')
    eq_(0, user.changelogs.count())

    cl.get(reverse('after-login'))

    eq_(1, user.changelogs.count())
    eq_('', cl.cookies['tracked-changelogs'].value)


def test_package_suggest_ignores_tracked_packages():
    cl = Client()
    thebot = Changelog.objects.create(name='thebot',
                                      namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot',
                                      downloader='git')
    thebot.versions.create(number='0.1.0', discovered_at=timezone.now())
    fields = Changelog.objects.create(name='fields',
                                      namespace='python',
                                      source='http://github.com/svetlyak40wt/django-fields',
                                      downloader='git')
    fields.versions.create(number='0.1.0', discovered_at=timezone.now())

    user = create_user('art')
    user.track(thebot)

    cl.login(username='art', password='art')

    response = cl.get(reverse('landing-package-suggest-list'))

    data = anyjson.deserialize(response.content)

    eq_(1, len(data['results']))


def test_anonymous_can_create_an_issue_and_it_is_tied_to_his_light_user():
    cl = Client()
    thebot = Changelog.objects.create(name='thebot', namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot')
    post_json(
        cl,
        reverse('issues-list'),
        expected_code=201,
        changelog=thebot.id,
        type='other',
        comment='The test')

    eq_(1, Issue.objects.count())
    issue = Issue.objects.all()[0]
    eq_(None, issue.user)
    assert issue.light_user != None

    eq_(1, UserHistoryLog.objects.filter(
        light_user=issue.light_user).count())


def test_normal_user_can_create_an_issue_and_it_is_tied_to_him():
    cl = Client()
    thebot = Changelog.objects.create(name='thebot', namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot')

    user = create_user('art')
    cl.login(username='art', password='art')

    chat.clear_messages()
    post_json(
        cl,
        reverse('issues-list'),
        expected_code=201,
        changelog=thebot.id,
        type='other',
        comment='The test')

    eq_(1, Issue.objects.count())
    issue = Issue.objects.all()[0]
    eq_(user, issue.user)
    assert issue.light_user != None

    eq_(1, UserHistoryLog.objects.filter(
        user=user).count())

    # also, it should post message into a chat
    eq_(1, len(chat.messages))


def test_nor_anonymous_nor_normal_user_are_unable_to_update_issue():
    cl = Client()
    moderator_bob = create_user('bob')
    thebot = Changelog.objects.create(name='thebot', namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot')
    thebot.add_to_moderators(moderator_bob)
    issue = thebot.issues.create(type='test', comment='some issue')

    put_json(
        cl,
        reverse('issues-detail', kwargs=dict(pk=issue.pk)),
        expected_code=403,
        changelog=thebot.id,
        type='other',
        comment='Changed')

    user = create_user('art')
    cl.login(username='art', password='art')

    put_json(
        cl,
        reverse('issues-detail', kwargs=dict(pk=issue.pk)),
        expected_code=403,
        changelog=thebot.id,
        type='other',
        comment='Changed')

    eq_(0, UserHistoryLog.objects.filter(
        user=user).count())


def test_url_field_validation_accepts_our_custom_urls():
    from allmychanges.api.serializers import URLField
    field = URLField()

    url = 'http://github.com/tadam/Ubic-Service-Plack'
    eq_(None, field.run_validators(url), 'Url {0} is not valid'.format(url))

    url = 'git://github.com/tadam/Ubic-Service-Plack.git'
    eq_(None, field.run_validators(url), 'Url {0} is not valid'.format(url))


def test_rename_changelog_using_put():
    cl = Client()
    moderator_bob = create_user('bob')
    changelog = Changelog.objects.create(name='thebot', namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot')
    changelog.add_to_moderators(moderator_bob)

    cl.login(username='bob', password='bob')

    put_json(
        cl,
        reverse('changelog-detail', kwargs=dict(pk=changelog.pk)),
        expected_code=200,
        namespace='other-namespace',
        name='other',
        source=changelog.source,
        downloader='vcs.git')


def test_api_normalizes_source_url_on_create():
    cl = Client()
    create_user('bob')
    cl.login(username='bob', password='bob')

    url = 'git://github.com/tadam/Ubic-Service-Plack.git'
    normalized_url = 'https://github.com/tadam/Ubic-Service-Plack'

    post_json(
        cl,
        reverse('changelog-list'),
        expected_code=201,
        namespace='test',
        name='package',
        source=url,
        downloader='vcs.git')
    ch = Changelog.objects.all()[0]
    eq_(normalized_url, ch.source)


def test_api_normalizes_source_url_on_search():
    cl = Client()
    create_user('bob')
    cl.login(username='bob', password='bob')

    url = 'git://github.com/tadam/Ubic-Service-Plack.git'
    normalized_url = 'https://github.com/tadam/Ubic-Service-Plack'

    Changelog.objects.create(namespace='test',
                             name='package',
                             source=normalized_url)

    response = cl.get(reverse('changelog-list'),
                      data=dict(source=url))
    check_status_code(200, response)
    eq_(1, len(json(response)))
