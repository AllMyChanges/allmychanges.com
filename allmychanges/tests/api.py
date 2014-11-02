# coding: utf-8
import anyjson
import mock
import time

from nose.tools import eq_
from django.test import Client, TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse

from allmychanges.models import Package, Changelog
from .utils import check_status_code, create_user

# схема урлов
# / - список доступных урлов
# /digest/
# /packages/
# /package/:namespace/:name/


def setup():
    Package.objects.all().delete()


def test_show_packages():
    cl = Client()

    user = create_user('art')
    changelog = Changelog.objects.create(namespace='python',
                                         name='pip',
                                         source='https://github.com/pipa/pip',
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

    response = cl.post('/v1/changelogs/',
                       dict(namespace='python',
                            name='pip',
                            source='https://github.com/pipa/pip'))
    check_status_code(201, response)
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
    response = cl.put('/v1/changelogs/{0}/'.format(changelog.id),
                      anyjson.serialize(dict(namespace='python',
                                             name='pip',
                                             source='https://github.com/pipa/pip')),
                      content_type='application/json')

    check_status_code(200, response)

    eq_(created_at, Changelog.objects.get(pk=changelog.pk).created_at)



class TransactionTests(TestCase):
#    use_transaction_isolation = False

    def tests_transactional_api_methods(self):
        """Check that API method is transactional and will leave
        database consistent if will broke in the middle"""

        cl = Client()

        create_user('art')
        cl.login(username='art', password='art')
        eq_(0, Package.objects.count())


        with mock.patch.object(Changelog.objects, 'get_or_create') as get_or_create:
            get_or_create.side_effect = RuntimeError
            try:
                cl.post('/v1/packages/',
                        dict(namespace='python',
                             name='pip',
                             source='https://github.com/pipa/pip'))
            except RuntimeError:
                pass

        eq_(0, Package.objects.count())
        eq_(0, Changelog.objects.count())



def test_authenticated_user_track_changelog():
    cl = Client()

    user = create_user('art')
    cl.login(username='art', password='art')

    changelog = Changelog.objects.create(source='http://github.com/svetlyak40wt/thebot')

    eq_(1, Changelog.objects.count())
    eq_(0, user.changelogs.count())

    response = cl.post('/v1/changelogs/{0}/track/'.format(changelog.id))
    check_status_code(200, response)
    eq_({'result': 'ok'}, anyjson.deserialize(response.content))

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

    response = cl.post(reverse('changelog-track', kwargs=dict(pk=changelog.id)))
    eq_(200, response.status_code, response.content)

    user = create_user('art')
    cl.login(username='art', password='art')
    eq_(0, user.changelogs.count())

    response = cl.get(reverse('after-login'))

    eq_(1, user.changelogs.count())
    eq_('', cl.cookies['tracked-changelogs'].value)


def test_package_suggest_ignores_tracked_packages():
    cl = Client()
    thebot = Changelog.objects.create(name='thebot', namespace='python',
                                      source='http://github.com/svetlyak40wt/thebot')
    thebot.versions.create(number='0.1.0', discovered_at=timezone.now(), code_version='v2')
    fields = Changelog.objects.create(name='fields', namespace='python',
                                      source='http://github.com/svetlyak40wt/django-fields')
    fields.versions.create(number='0.1.0', discovered_at=timezone.now(), code_version='v2')

    user = create_user('art')
    user.track(thebot)

    cl.login(username='art', password='art')

    response = cl.get(reverse('landing-package-suggest-list'))

    data = anyjson.deserialize(response.content)

    eq_(1, len(data['results']))
