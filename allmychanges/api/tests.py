# coding: utf-8
import anyjson

from nose.tools import eq_
from django.test import Client
from django.utils import timezone

from allmychanges.models import Package
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
                         created_at=timezone.now(),
                         next_update_at=timezone.now())
    
    user = create_user('gena')
    user.packages.create(namespace='python',
                         name='rest',
                         source='https://github.com/frame/work',
                         created_at=timezone.now(),
                         next_update_at=timezone.now())

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
