# coding: utf-8

from nose.tools import eq_
from operator import itemgetter
from django.test import Client
from ..utils import create_user, get_json, post_json
from allmychanges.models import Changelog, Tag
from unittest import TestCase
from hamcrest import (
    assert_that,
    contains,
    has_properties,
    equal_to,
)


def attr_or_item_getter(name, default=None):
    def getter(obj):
        if hasattr(obj, name):
            return getattr(obj, name)
        return obj.get(name, default)
    return getter


get_names = attr_or_item_getter('name')
get_versions = itemgetter('version_number')


class TestUserTags(TestCase):
    def setUp(self):
        self.cl = Client()
        self.user = create_user('art')
        self.cl.login(username='art', password='art')

        self.changelog = Changelog.objects.create(namespace='python',
                                           name='pip',
                                           source='https://github.com/some/url')
        self.versions = []

        for i in range(10):
            v = self.changelog.versions.create(number='0.1.{0}'.format(i))
            self.versions.append(v)

    def test_if_no_tags_return_empty_list(self):
        data = get_json(self.cl, '/v1/tags/')
        eq_([], data['results'])

    def test_if_there_are_some_tags(self):
        self.versions[3].set_tag(self.user, 'amch')
        self.versions[3].set_tag(self.user, 'foo')
        self.versions[5].set_tag(self.user, 'bar')

        data = get_json(self.cl, '/v1/tags/')
        eq_(['amch', 'foo', 'bar'],
            map(get_names, data['results']))

    def test_that_other_user_does_not_see_mine(self):
        ivan = create_user('ivan')
        self.versions[0].set_tag(ivan, 'foo')

        # now I create a tag myself
        self.versions[0].set_tag(self.user, 'bar')

        # and should see only the 'bar' tag
        data = get_json(self.cl, '/v1/tags/')
        eq_(['bar'], map(get_names, data['results']))


    def test_that_i_can_filter_tags_by_project_id(self):
        clint = Changelog.objects.create(
            namespace='python',
            name='clint',
            source='https://github.com/some/clint')
        first_version = clint.versions.create(number='0.1.0')
        first_version.set_tag(self.user, 'blah')

        self.versions[0].set_tag(self.user, 'minor')
        data = get_json(self.cl, '/v1/tags/?project_id={0}'.format(
            clint.id))
        eq_(['blah'], map(get_names, data['results']))


    def test_when_other_version_tagged_with_same_tag_it_is_moved(self):
        self.versions[0].set_tag(self.user, 'blah')
        self.versions[5].set_tag(self.user, 'blah')

        data = get_json(self.cl, '/v1/tags/')
        eq_(['blah'], map(get_names, data['results']))
        eq_(['0.1.5'], map(get_versions, data['results']))

    def test_same_version_can_have_different_tags(self):
        self.versions[0].set_tag(self.user, 'blah')
        self.versions[0].set_tag(self.user, 'minor')
        self.versions[0].set_tag(self.user, 'again')

        data = get_json(self.cl, '/v1/tags/')
        eq_(['blah', 'minor', 'again'],
            map(get_names, data['results']))


    def test_special_handle_can_tag_a_version(self):
        version = self.versions[3]

        post_json(
            self.cl,
            '/v1/changelogs/{}/tag/'.format(self.changelog.pk),
            expected_code=201,
            name='blah',
            version=version.number)

        eq_(['blah'],
            map(get_names, version.tags.all()))

    def test_special_handle_can_untag_a_version(self):
        version = self.versions[3]
        version.set_tag(self.user, 'foo')

        post_json(
            self.cl,
            '/v1/changelogs/{}/untag/'.format(self.changelog.pk),
            expected_code=204,
            name='foo')

        # check if tag was removed
        eq_([],
            map(get_names, version.tags.all()))

    def test_untag_of_unknown_tag_is_ok(self):
        version = self.versions[3]
        version.set_tag(self.user, 'foo') # here we have 'foo' tag

        # but remove 'bar' tag
        post_json(
            self.cl,
            '/v1/changelogs/{}/untag/'.format(self.changelog.pk),
            expected_code=204,
            name='bar')

        # and foo tag is still there
        eq_(['foo'],
            map(get_names, version.tags.all()))


    def test_unknown_version_can_be_tagged_and_assigned_to_version_later(self):
        # checking if we can create a tag with version which is not known
        self.changelog.set_tag(self.user, 'blah', '0.2.0')

        # this tag should be set on changelog
        # but have no version assigned
        all_tags = list(self.changelog.tags.all())
        assert_that(
            all_tags,
            contains(
                has_properties(
                    name='blah',
                    version=None,
                )
            )
        )
        # after we create the version with this number
        version = self.changelog.versions.create(
            number='0.2.0'
        )
        # this version should have this tag
        tag = Tag.objects.get(pk=all_tags[0].pk)
        assert_that(
            tag.version,
            equal_to(version))
