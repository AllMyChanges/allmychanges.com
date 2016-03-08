# coding: utf-8
import datetime
import mock
import os.path
import anyjson

from nose.tools import eq_
from django.test import Client, TransactionTestCase, TestCase
from django.core.urlresolvers import reverse
from django.utils import timezone

from allmychanges.auth.pipeline import add_default_package
from allmychanges.parsing.pipeline import (
    filter_versions_by_source,
    filter_versions_by_attribute)
from allmychanges.models import (Version,
                                 User,
                                 Changelog,
                                 Preview)
from allmychanges.utils import (
    dt_in_window,
    change_weekday,
    first_sentences,
    discard_seconds)
from allmychanges.downloaders.fake import download as fake_downloader
from allmychanges.changelog_updater import (
    update_changelog_from_raw_data3)
from allmychanges.parsing.pipeline import get_files
from allmychanges.env  import Environment

from allmychanges.source_guesser import guess_source

from allmychanges.views import get_digest_for

from .utils import refresh, check_status_code, create_user


def test_update_package_from_basic_structure():
    root = Environment()
    structure = [
        root.push(version='0.1.0',
                  content='v1 content',
                  processed_content='v1 processed content'),
        root.push(version='0.2.0',
                  content='v2 content',
                  processed_content='v2 processed content')
    ]

    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')
    art.track(changelog)

    update_changelog_from_raw_data3(changelog, structure)

    eq_(2, changelog.versions.count())
    v = changelog.versions.all()[0]
    eq_('0.2.0', v.number)
    eq_('v2 processed content', v.processed_text)


def test_update_package_leaves_version_dates_as_is_if_there_isnt_new_date_in_raw_data():
    root = Environment()
    structure = [
        root.push(version='0.1.0',
                  content='content',
                  processed_content='processed content')]

    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')
    art.track(changelog)

    update_changelog_from_raw_data3(changelog, structure)

    v = changelog.versions.all()[0]
    discovered_at = v.discovered_at
    assert v.date is None
    assert discovered_at is not None

    with mock.patch('allmychanges.changelog_updater.timezone') as timezone:
        timezone.now.return_value = datetime.datetime.now() + datetime.timedelta(10)
        update_changelog_from_raw_data3(changelog, structure)

    v = changelog.versions.all()[0]
    # neither date not discovered_at were changed
    assert v.date is None
    eq_(discovered_at, v.discovered_at)


def test_update_package_changes_date_if_it_was_changed_in_the_raw_data():
    root = Environment()
    structure = [
        root.push(version='0.1.0',
                  content='content',
                  processed_content='processed content')]

    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')
    art.track(changelog)

    update_changelog_from_raw_data3(changelog, structure)

    v = changelog.versions.all()[0]
    discovered_at = v.discovered_at
    assert v.date is None
    assert discovered_at is not None

    new_date = datetime.date(2013, 3, 27)
    structure[0].date = new_date
    update_changelog_from_raw_data3(changelog, structure)
    v = changelog.versions.all()[0]

    # package's date has changed
    eq_(new_date, v.date)
    # but discovery date didn't change
    eq_(discovered_at, v.discovered_at)


def test_fake_downloader():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md')
    art.track(changelog)
    path = fake_downloader(changelog.source)
    assert path
    with open(os.path.join(path, 'CHANGELOG')) as f:
        content = f.read()
        eq_("""0.1.1
=====

  * Some bugfix.

0.1.0
=====

  * Initial release.""", content)



def test_environment_cloning():
    env = Environment()
    env.some = 'value'

    env2 = env.push()
    eq_('value', env2.some)

    env2.some = 'another'
    eq_('another', env2.some)
    eq_('value', env.some)

    # checking another way of creating child environment
    # and setting the values simultaneously
    env3 = env2.push(some='new value',
                     other='item')
    eq_('new value', env3.some)
    eq_('item', env3.other)
    eq_('another', env2.some)


def test_environment_comparison():
    eq_(Environment(), Environment())

    env1 = Environment()
    env1.type = 'blah'
    env2 = Environment()
    env2.type = 'blah'
    eq_(env1, env2)

    # first env inherits it's type
    # second have it explicitly
    env1 = Environment()
    env1.type = 'blah'
    env2 = Environment().push(type='blah')
    eq_(env1.push(), env2)

    # first env have two vars
    # second only one
    env1 = Environment().push(type='blah', foo='bar')
    env2 = Environment().push(type='blah')
    assert env1 != env2


def test_get_env_keys():
    eq_(['bar', 'baz', 'foo'],
        Environment() \
            .push(foo=1) \
            .push(bar=2) \
            .push(baz=3) \
            .keys())


def test_source_guesser():
    content = """Some text with package description
    which have urls like <a href="http://github.com/alex/django-filter/tree/master">that</a>
    and <a href="https://github.com/alex/django-filter">that</a>

    But also it could include links <a href="http://bitbucket.org/antocuni/pdb">to the bitbucked</a>
    To some <a href="https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-dev-screenshot.png">raw materials</a>.
    And raw <a href="http://bitbucket.org/antocuni/pdb/raw/0c86c93cee41/screenshot.png">at bitbucket</a>.
    """
    with mock.patch('allmychanges.source_guesser.requests') as requests:
        response = mock.Mock()
        response.content = content
        requests.get.return_value = response
        urls = guess_source('python', 'test')

        eq_(['https://github.com/alex/django-filter',
             'https://bitbucket.org/antocuni/pdb',
             'https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-dev-screenshot.png'],
            urls)


class UserTests(TestCase):
    def test_two_users_can_have_blank_emails(self):
        User.objects.create(username='bob', email='')
        User.objects.create(username='karl', email='')
        eq_(2, User.objects.count())

    def test_but_two_users_should_have_different_emails(self):
        User.objects.create(username='bob', email='mail@me.com')
        self.assertRaises(ValueError,
                          User.objects.create,
                          username='karl', email='mail@me.com')


class ProfileTests(TransactionTestCase):
    def setUp(self):
        self.user = create_user('art')
        self.user.save()

        self.cl = Client()
        self.cl.login(username='art', password='art')

    def test_timezone_update(self):
        url = '/account/settings/'
        response = self.cl.post(url, dict(timezone='Europe/Moscow',
                                          send_digest='daily',
                                          slack_url=''))
        check_status_code(302, response)
        assert url in response['Location']
        user = refresh(self.user)
        eq_('Europe/Moscow', user.timezone)



def test_tz_window():
    dt = datetime.datetime
    now = dt(2014, 05, 19, 6, 0) # system datetime (UTC)

    eq_(False,
        dt_in_window('Europe/Moscow',        # user's timezone
                     now,
                     9))                     # desired hour in user's timezone

    # Kiev 1 hour ealier than Moscow
    eq_(True, dt_in_window('Europe/Kiev', now, 9))


def test_new_user_have_allmychanges_in_digest():
    user = create_user('art')
    eq_(0, user.changelogs.count())

    add_default_package(None, is_new=True, user=user)

    eq_(1, user.changelogs.count())
    eq_('allmychanges', user.changelogs.all()[0].name)


def test_old_user_can_have_zero_packages():
    """We wont add a default package to old users."""
    user = create_user('art')
    eq_(0, user.changelogs.count())

    add_default_package(None, is_new=False, user=user)

    eq_(0, user.changelogs.count())


def test_digest_for_today_includes_changes_from_last_9am():
    user = create_user('art')
    today = datetime.datetime(2014, 1, 1, 9, 0, tzinfo=timezone.UTC()) # 9am
    one_day = datetime.timedelta(1)
    one_minute = datetime.timedelta(0, 60)

    foo = Changelog.objects.create(namespace='test', name='foo', source='foo')
    foo.versions.create(number='0.1.0',
                        discovered_at=today - one_day - one_minute)

    bar = Changelog.objects.create(namespace='test', name='bar', source='bar')
    bar.versions.create(number='0.3.0',
                        discovered_at=today - one_day)

    user.track(foo)
    user.track(bar)

    digest = get_digest_for(user.changelogs,
                            after_date=today - one_day)
    eq_(1, len(digest))


def api_get(handle, **kwargs):
    cl = Client()
    response = cl.get(reverse(handle), kwargs)
    if response.status_code >= 200 and response.status_code < 300:
        if response.content_type == 'application/json':
            return anyjson.deserialize(response.content)
    return response


def test_namespace_name_validator():
    Changelog.objects.create(namespace='foo',
                             name='bar')

    eq_({'result': 'ok'},
        api_get('validate-changelog-name-list',
                 namespace='foo',
                 name='blah'))

    eq_({'result': 'ok'},
        api_get('validate-changelog-name-list',
                 namespace='blah',
                 name='bar'))

    eq_({'errors': {'name': ['These namespace/name pair already taken.']}},
        api_get('validate-changelog-name-list',
                 namespace='foo',
                 name='bar'))

    eq_({'errors': {'namespace': ['Please, fill this field'],
                    'name': ['Please, fill this field']}},
        api_get('validate-changelog-name-list',
                 namespace='',
                 name=''))

    eq_({'errors': {'namespace': ['Field should not contain backslashes'],
                    'name': ['Field should not contain backslashes']}},
        api_get('validate-changelog-name-list',
                 namespace='fo/o',
                 name='ba/r'))



def test_landing_digest_keeps_tracked_in_cookie():
    cl = Client()
    response = cl.get(reverse('landing-digest') + '?changelogs=1,2,3')
    eq_('1,2,3', response.cookies['tracked-changelogs'].value)


def test_get_files_respect_ignore_and_search_lists():
    def walk(root):
        return [('samples/markdown-release-notes/', ['docs'], ['unrelated-crap.md']),
                ('samples/markdown-release-notes/docs',
                 [], ['0.1.0.md', '0.1.1.md'])]

    env = Environment()
    env.dirname = 'samples/markdown-release-notes'
    env.ignore_list = []
    env.search_list = []
    result = [item.filename for item in get_files(env, walk)]
    eq_(['samples/markdown-release-notes/unrelated-crap.md',
         'samples/markdown-release-notes/docs/0.1.0.md',
         'samples/markdown-release-notes/docs/0.1.1.md'],
        result)


    env.ignore_list = ['unrelated-crap.md']
    env.search_list = []
    result = [item.filename for item in get_files(env, walk)]
    eq_(['samples/markdown-release-notes/docs/0.1.0.md',
         'samples/markdown-release-notes/docs/0.1.1.md'],
        result)


    env.ignore_list = ['docs']
    env.search_list = []
    result = [item.filename for item in get_files(env, walk)]
    eq_(['samples/markdown-release-notes/unrelated-crap.md'],
        result)

    env.ignore_list = []
    env.search_list = [('unrelated-crap.md', None)]
    result = [item.filename for item in get_files(env, walk)]
    eq_(['samples/markdown-release-notes/unrelated-crap.md'],
        result)

    env.ignore_list = []
    env.search_list = [('doc', None)]
    result = [item.filename for item in get_files(env, walk)]
    eq_(['samples/markdown-release-notes/docs/0.1.0.md',
         'samples/markdown-release-notes/docs/0.1.1.md'],
        result)


def test_filtering_versions_by_source():
    # now check if CHANGELOG.md is preferred to large number of versions
    # from docs/ subdirectory
    versions = []
    versions.append(Version(filename="CHANGELOG.md", number="1.3.0"))
    versions.append(Version(filename="CHANGELOG.md", number="1.2.0"))
    versions.append(Version(filename="CHANGELOG.md", number="1.1.2"))
    versions.append(Version(filename="CHANGELOG.md", number="1.1.1"))
    versions.append(Version(filename="docs/sources/installation/ubuntulinux.md", number="14.04"))
    versions.append(Version(filename="docs/sources/installation/ubuntulinux.md", number="13.04"))
    versions.append(Version(filename="docs/sources/installation/ubuntulinux.md", number="12.04"))
    versions.append(Version(filename="docs/sources/installation/debian.md", number="8.0"))
    versions.append(Version(filename="docs/sources/reference/api/hub_registry_spec.md", number="6.2"))
    versions.append(Version(filename="docs/sources/reference/api/hub_registry_spec.md", number="4.4"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.5.md", number="3.3"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.1.md", number="3.2"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.1.md", number="3.1"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.1.md", number="2.3"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.1.md", number="2.2"))
    versions.append(Version(filename="docs/sources/reference/api/docker_remote_api_v1.1.md", number="2.1"))

    new = filter_versions_by_source(versions)
    filenames = {v.filename for v in new}
    eq_(['CHANGELOG.md'], list(filenames))


def test_filtering_versions_by_source_on_separate_release_notes():
    versions = []
    versions.append(Version(filename='dist/kafka/0.8.2.1/RELEASE_NOTES.html', number='0.8.2.1'))
    versions.append(Version(filename='dist/kafka/0.8.0/RELEASE_NOTES.html', number='0.8.0'))

    new = filter_versions_by_source(versions)
    filenames = {v.filename for v in new}
    eq_(['dist/kafka/0.8.0/RELEASE_NOTES.html',
         'dist/kafka/0.8.2.1/RELEASE_NOTES.html'], list(filenames))


def test_filtering_versions_by_attribute():
    root = Environment()
    versions = [
        root.push(title='RELEASE_NOTES.html', number='0.8.2.1'),
        root.push(title='Version 0.8.0 release notes', number='0.8.0')]

    new = filter_versions_by_attribute(versions,
                                       search_list=[(ur'[title=Version \d.*]', None)])
    eq_(['0.8.0'], [v.number for v in new])

    new = filter_versions_by_attribute(versions,
                                       ignore_list=[ur'[title=.*\.html]'])
    eq_(['0.8.0'], [v.number for v in new])

    new = filter_versions_by_attribute(versions,
                                       search_list=[],
                                       ignore_list=[])
    eq_(set(['0.8.0', '0.8.2.1']), {v.number for v in new})



def test_digest_does_not_include_preview_versions():
    today = datetime.datetime(2014, 1, 1, 9, 0, tzinfo=timezone.UTC()) # 9am
    week = datetime.timedelta(7)
    day = datetime.timedelta(1)

    foo = Changelog.objects.create(namespace='test', name='foo', source='foo')
    foo.versions.create(number='0.1.0',
                        discovered_at=today - week)

    preview = Preview.objects.create(changelog=foo)
    preview.versions.create(changelog=foo,
                            number='0.1.0',
                            discovered_at=today)

    digest = get_digest_for(Changelog.objects.filter(pk=foo.pk),
                            after_date=today - day)

    eq_(0, len(digest))


def test_active_changelogs_filtering():
    ch1 = Changelog.objects.create(namespace='test', name='foo1', source='foo1')
    Changelog.objects.create(namespace='test', name='foo2', source='foo2',
                             paused_at=timezone.now())
    Changelog.objects.create(namespace='test', name=None, source='foo3')

    response = list(Changelog.objects.only_active())
    eq_(1, len(response))
    eq_(ch1.id, response[0].id)



def test_first_sentences():
    eq_(u'Blah.', first_sentences(u'Blah.', max_length=5))
    eq_(u'Blah minor.', first_sentences(u'Blah minor. Again!', max_length=11))
    eq_(u'Blah mino…', first_sentences(u'Blah minor. Again!', max_length=10))
    eq_(u'Again!', first_sentences(u'Again! Blah minor.', max_length=7))
    eq_(u'Blah minor.', first_sentences(u'Blah minor.\nAgain!', max_length=11))
    eq_(u'Blah minor. Again!', first_sentences(u'Blah minor.\nAgain!\nAnd again.', max_length=20))


def test_change_weekday():
    # this date has weekday==2
    now = datetime.datetime(2016, 3, 2)

    eq_(now, change_weekday(now, now.weekday()))
    eq_(datetime.datetime(2016, 3, 1), change_weekday(now, 1))
    eq_(datetime.datetime(2016, 2, 29), change_weekday(now, 0))

    eq_(datetime.datetime(2016, 3, 3), change_weekday(now, 3))
    eq_(datetime.datetime(2016, 3, 4), change_weekday(now, 4))
    eq_(datetime.datetime(2016, 3, 5), change_weekday(now, 5))
    eq_(datetime.datetime(2016, 3, 6), change_weekday(now, 6))
