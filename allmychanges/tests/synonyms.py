# coding: utf-8

from nose.tools import eq_
from django.test import Client
from django.core.urlresolvers import reverse
from urllib import urlencode

from allmychanges.models import Changelog


def test_search_use_synonyms():
    cl = Client()

    changelog = Changelog.objects.create(namespace='javascript',
                                         name='nodejs',
                                         source='https://github.com/nodejs/node')
    changelog.add_synonym('node')
    changelog.add_synonym('iojs')
    changelog.add_synonym(r'https://github.com/nodejs/node/blob/')

    changelog_url = 'http://testserver/p/javascript/nodejs/'
    search_url = reverse('search')

    response = cl.get(search_url + '?q=nodejs')
    eq_(changelog_url, response.url)

    response = cl.get(search_url + '?q=node')
    eq_(changelog_url, response.url)

    response = cl.get(search_url + '?q=iojs')
    eq_(changelog_url, response.url)

    response = cl.get(search_url + '?' + urlencode(dict(q='https://github.com/nodejs/node/blob/master/CHANGELOG.md')))
    eq_(changelog_url, response.url)
    assert False
