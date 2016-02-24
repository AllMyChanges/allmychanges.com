# coding: utf-8

from nose.tools import eq_, assert_raises
from django.test import Client
from django.core.urlresolvers import reverse
from urllib import urlencode

from allmychanges.models import Changelog
from allmychanges.exceptions import SynonymError
from allmychanges.tests.utils import create_user


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


def test_add_synonym_page_contains_existing_synonyms():
    cl = Client()

    changelog = Changelog.objects.create(namespace='javascript',
                                         name='nodejs',
                                         source='https://github.com/nodejs/node')
    synonym = 'blah-minor-nodejs'
    changelog.add_synonym(synonym)

    response = cl.get(reverse('synonyms',
                              kwargs=dict(
                                  namespace='javascript',
                                  name='nodejs')))
    assert synonym in response.content


def test_add_synonym_using_POST():
    cl = Client()

    changelog = Changelog.objects.create(namespace='javascript',
                                         name='nodejs',
                                         source='https://github.com/nodejs/node')
    changelog.add_synonym('old-synonym')

    url = reverse('synonyms',
                  kwargs=dict(
                      namespace='javascript',
                      name='nodejs'))

    response = cl.post(url, dict(synonym='new-synonym'))
    assert response.url.endswith(url)

    eq_(['new-synonym', 'old-synonym'],
        sorted(changelog.synonyms.all().values_list('source', flat=True)))


def test_only_moderator_can_add_synonyms():
    cl = Client()
    owner = create_user('owner')
    art = create_user('art')

    changelog = Changelog.objects.create(namespace='javascript',
                                         name='nodejs',
                                         source='https://github.com/nodejs/node')
    changelog.add_to_moderators(owner)

    url = reverse('synonyms',
                  kwargs=dict(
                      namespace=changelog.namespace,
                      name=changelog.name))

    # checking from name of anonymous
    response = cl.get(url)
    eq_(response.status_code, 403)
    response = cl.post(url, dict(synonym='new-synonym'))
    eq_(response.status_code, 403)

    # checking as usual user
    cl.login(username='art', password='art')

    response = cl.get(url)
    eq_(response.status_code, 403)
    response = cl.post(url, dict(synonym='new-synonym'))
    eq_(response.status_code, 403)

    # checking as a moderator
    changelog.add_to_moderators(art)

    response = cl.get(url)
    eq_(response.status_code, 200)
    response = cl.post(url, dict(synonym='new-synonym'))
    eq_(response.status_code, 302)


def test_when_we_try_to_add_synonym_twice_no_error_raised():
    changelog = Changelog.objects.create(namespace='javascript',
                                         name='nodejs',
                                         source='https://github.com/nodejs/node')
    changelog.add_synonym('node')
    changelog.add_synonym('node')


def test_when_we_try_to_add_synonym_bound_to_another_changelog_error_raised():
    Changelog.objects.create(namespace='foo',
                                   name='foo',
                                   source='foo')
    bar = Changelog.objects.create(namespace='bar',
                                   name='bar',
                                   source='bar')
    assert_raises(SynonymError, bar.add_synonym, 'foo')



def test_impossible_to_create_synonym_which_matches_to_existing_project_source():
    changelog = Changelog.objects.create(
        namespace='javascript',
        name='nodejs',
        source='https://github.com/nodejs/node')

    assert_raises(SynonymError,
                  changelog.add_synonym,
                  'https://github.com/nodejs/node')
