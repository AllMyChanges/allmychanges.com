# coding: utf-8

from nose.tools import eq_
from django.test import Client
from ..utils import check_status_code, create_user, put_json
from allmychanges.models import Changelog


def test_put_saves_downloaders():
    cl = Client()

    create_user('art')
    cl.login(username='art', password='art')

    changelog = Changelog.objects.create(namespace='python',
                                       name='pip',
                                       source='https://github.com/some/url')

    response = put_json(cl,
                        '/v1/changelogs/{0}/'.format(changelog.id),
                        downloader='hg',
                        downloaders=[{'name': 'hg'}],
                        namespace='python',
                        name='pip',
                        source='https://github.com/pipa/pip')
    check_status_code(200, response)

    ch = Changelog.objects.get(pk=changelog.pk)
    eq_(ch.downloaders, [{'name': 'hg'}])
