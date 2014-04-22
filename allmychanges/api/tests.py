# coding: utf-8
import anyjson
import mock
import time

from nose.tools import eq_
from django.test import Client, TestCase
from django.utils import timezone

from allmychanges.models import Package, Changelog
from allmychanges.tests import check_status_code, create_user

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
    user.packages.create(namespace='python',
                         name='pip',
                         source='https://github.com/pipa/pip',
                         created_at=timezone.now())
    
    user = create_user('gena')
    user.packages.create(namespace='python',
                         name='rest',
                         source='https://github.com/frame/work',
                         created_at=timezone.now())

    # user art should be able to see only his own packages
    cl.login(username='art', password='art')
    response = cl.get('/v1/packages/')
    eq_(200, response.status_code)
    data = anyjson.deserialize(response.content)
    eq_(1, len(data))
    eq_('pip', data[0]['name'])


def test_add_package():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')
    eq_(0, Package.objects.count())

    response = cl.post('/v1/packages/',
                      dict(namespace='python',
                           name='pip',
                           source='https://github.com/pipa/pip'))
    check_status_code(201, response)
    eq_(1, Package.objects.count())


def test_put_does_not_affect_created_at_field():
    cl = Client()

    user = create_user('art')
    cl.login(username='art', password='art')
    
    package = user.packages.create(namespace='python',
                                   name='pip',
                                   source='https://github.com/some/url')
    created_at = Package.objects.get(pk=package.pk).created_at

    time.sleep(1)
    response = cl.put('/v1/packages/{0}/'.format(package.id),
                      anyjson.serialize(dict(namespace='python',
                                             name='pip',
                                             source='https://github.com/pipa/pip')),
                      content_type='application/json')
    
    check_status_code(200, response)
    
    eq_(created_at, Package.objects.get(pk=package.pk).created_at)


def test_two_users_are_able_to_add_package_with_same_source():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')
    eq_(0, Package.objects.count())

    response = cl.post('/v1/packages/',
                      dict(namespace='python',
                           name='pip',
                           source='https://github.com/pipa/pip'))
    check_status_code(201, response)

    create_user('peter')
    cl.login(username='peter', password='peter')

    response = cl.post('/v1/packages/',
                      dict(namespace='python',
                           name='pip',
                           source='https://github.com/pipa/pip'))
    check_status_code(201, response)
    eq_(2, Package.objects.count())


class TransactionTests(TestCase):
    use_transaction_isolation = False
    
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
