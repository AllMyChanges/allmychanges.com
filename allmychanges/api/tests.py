# coding: utf-8
import anyjson

from nose.tools import eq_
from allmychanges.models import Package
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone


# схема урлов
# / - список доступных урлов
# /digest/
# /packages/
# /package/:namespace/:name/

def check_status_code(desired_code, response):
    eq_(desired_code,
        response.status_code,
        'Status code {0} != {1}, content: {2}'.format(
            response.status_code,
            desired_code,
            response.content))


def create_user(username):
    """Создает пользователя с заданным username и таким же паролем."""
    try:
        return get_user_model().objects.get(username=username)

    except get_user_model().DoesNotExist:
        user = get_user_model().objects.create_user(
            username, username + '@example.yandex.ru', username)
        user.center_id = 10000 + user.id
        user.save()
        return user


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
    eq_(1, len(data['results']))
    eq_('pip', data['results'][0]['name'])


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
