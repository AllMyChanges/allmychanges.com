# coding: utf-8
import datetime
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


def json(response):
    return anyjson.deserialize(response.content)


def put_json(cl, url, **data):
    response = cl.put(url,
                      anyjson.serialize(data),
                      content_type='application/json')
    return response


def post_json(cl, url, **data):
    response = cl.post(url,
                       anyjson.serialize(data),
                       content_type='application/json')
    return response


def dt_eq(left_date, right_date, threshold=3):
    if not isinstance(left_date, datetime.datetime):
        raise AssertionError('First argument should be an instance of `datetime` class, but it is `{0}`.'.format(
            type(left_date).__name__))

    if not isinstance(right_date, datetime.datetime):
        raise AssertionError('Second argument should be an instance of `datetime` class, but it is `{0}`.'.format(
            type(right_date).__name__))

    diff = abs(left_date - right_date).total_seconds()
    assert diff < threshold, '{0} differ from {1} more than in {2} seconds'.format(
        left_date, right_date, threshold)
