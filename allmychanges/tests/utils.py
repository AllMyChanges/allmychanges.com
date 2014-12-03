# coding: utf-8
import anyjson

from nose.tools import eq_
from allmychanges.models import User


def refresh(obj):
    return obj.__class__.objects.get(pk=obj.pk)


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
        return User.objects.get(username=username)

    except User.DoesNotExist:
        user = User.objects.create_user(
            username, username + '@example.yandex.ru', username)
        user.save()
        return user


def put_json(cl, url, **data):
    response = cl.put(url,
                      anyjson.serialize(data),
                      content_type='application/json')
    return response
