# coding: utf-8

from nose.tools import eq_
from django.test import Client
from ..utils import create_user, put_json, post_json
from allmychanges.models import Changelog

from hamcrest import assert_that, has_properties


def test_put_saves_downloaders():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')

    changelog = Changelog.objects.create(namespace='python',
                                       name='pip',
                                       source='https://github.com/some/url')

    put_json(
        cl,
        '/v1/changelogs/{0}/'.format(changelog.id),
        expected_code=200,
        downloader='hg',
        downloaders=[{'name': 'hg'}],
        namespace='python',
        name='pip',
        source='https://github.com/pipa/pip')

    ch = Changelog.objects.get(pk=changelog.pk)
    eq_(ch.downloaders, [{'name': 'hg'}])


def test_post_is_able_to_create_project_without_source():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')

    eq_(0, Changelog.objects.count())

    post_json(
        cl,
        '/v1/changelogs/',
        expected_code=201,
        namespace='python',
        name='pip')

    # now there is one record in a database
    eq_(1, Changelog.objects.all().count())
    # but it is not good changelog yet
    eq_(0, Changelog.objects.good().count())

    ch = Changelog.objects.all()[0]
    assert_that(
        ch,
        has_properties(
            namespace='python',
            name='pip',
            source=''))
