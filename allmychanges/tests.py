# coding: utf-8
import datetime
import mock
import os.path

from nose.tools import eq_
from django.test import Client, TransactionTestCase, TestCase

from allmychanges.models import Package, User
from allmychanges.utils import (
    update_changelog_from_raw_data,
    update_changelog,
    fake_downloader,
    guess_source,
    fill_missing_dates,
    dt_in_window,
    extract_changelog_from_vcs)


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

def test_update_package_from_basic_structure():
    structure = [
        {'version': '0.1.0',
         'sections': [
             {'notes': 'Initial release'}]},
        {'version': '0.2.0',
         'sections': [
             {'notes': 'Fixes:',
              'items': ['boo fixed', 'baz fixed too']},
             {'notes': 'Features:',
              'items': ['cool feature was added']}]}
    ]

    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test',
        user=art)
    
    update_changelog_from_raw_data(package.changelog, structure)
    
    eq_(2, package.changelog.versions.count())
    v = package.changelog.versions.all()[0]
    eq_('0.2.0', v.number)
    eq_(['boo fixed', 'baz fixed too'],
        [item.text
         for item in v.sections.all()[0].items.all()])


def test_update_package_leaves_version_dates_as_is_if_there_isnt_new_date_in_raw_data():
    structure = [
        {'version': '0.1.0',
         'sections': [
             {'notes': 'Initial release'}]}
    ]

    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test',
        user=art)
    
    update_changelog_from_raw_data(package.changelog, structure)
    
    v = package.changelog.versions.all()[0]
    date = v.date
    assert date is not None

    with mock.patch('allmychanges.utils.timezone') as timezone:
        timezone.now.return_value = datetime.datetime.now() + datetime.timedelta(10)
        update_changelog_from_raw_data(package.changelog, structure)
        
    v = package.changelog.versions.all()[0]
    eq_(date, v.date)


def test_update_package_changes_date_if_it_was_changed_in_the_raw_data():
    structure = [
        {'version': '0.1.0',
         'sections': [
             {'notes': 'Initial release'}]}
    ]

    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test',
        user=art)
    
    update_changelog_from_raw_data(package.changelog, structure)
    
    v = package.changelog.versions.all()[0]
    date = v.date
    assert date is not None
    
    new_date = datetime.date(2013, 3, 27)
    structure[0]['date'] = new_date
    update_changelog_from_raw_data(package.changelog, structure)
    v = package.changelog.versions.all()[0]
    eq_(new_date, v.date)


def test_fake_downloader():
    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md',
        user=art)
    path = fake_downloader(package)
    assert path
    with open(os.path.join(path, 'CHANGELOG')) as f:
        content = f.read()
        eq_("""0.1.1
=====

  * Some bugfix.

0.1.0
=====

  * Initial release.""", content)



def test_update_package_using_full_pipeline():
    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md',
        user=art)
    
    update_changelog(package.changelog)
    eq_(2, package.changelog.versions.count())
    eq_('Some bugfix.', package.changelog.versions.all()[0].sections.all()[0].items.all()[0].text)
    eq_('Initial release.', package.changelog.versions.all()[1].sections.all()[0].items.all()[0].text)


def test_changing_source_on_package_will_create_another_changelog():
    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md',
        user=art)
    
    old_changelog = package.changelog
    assert old_changelog is not None

    package.source = 'test+samples/another.md'
    package.save()
    new_changelog = package.changelog
    
    assert new_changelog != old_changelog
    eq_(1, new_changelog.packages.count())
    eq_(0, old_changelog.packages.count())


def test_extract_from_vcs():
    date = datetime.date
    raw_data = extract_changelog_from_vcs(
        [(None,    date(2014, 1, 15), 'Initial commit'),
         (None,    date(2014, 1, 15), 'Feature was added'),
         ('0.1.0', date(2014, 1, 16), 'Tests were added'),
         (None,    date(2014, 2, 9),  'Repackaging'), # such gaps should be considered
                                                      # as having previous version
         ('0.2.0', date(2014, 2, 10), 'Some new functions'),
         ('0.2.0', date(2014, 2, 11), 'Other feature'),
         ('0.3.0', date(2014, 2, 14), 'Version bump'),
         ('0.3.0', date(2014, 3, 20), 'First unreleased feature'),
         ('0.3.0', date(2014, 3, 21), 'Second unreleased feature')])

    eq_([{'version': '0.1.0',
          'date': date(2014, 1, 16),
          'sections': [{'items': ['Initial commit',
                                  'Feature was added',
                                  'Tests were added']}]},
         {'version': '0.2.0',
          'date': date(2014, 2, 10),
          'sections': [{'items': ['Repackaging',
                                  'Some new functions']}]},
         {'version': '0.3.0',
          'date': date(2014, 2, 14),
          'sections': [{'items': ['Other feature',
                                  'Version bump']}]},
         {'version': 'x.x.x',
          'unreleased': True,
          'date': date(2014, 3, 21),
          'sections': [{'items': ['First unreleased feature',
                                  'Second unreleased feature']}]},
     ],
        
        raw_data)


def test_source_guesser():
    content = """Some text with package description
    which have urls like <a href="http://github.com/alex/django-filter/tree/master">that</a>
    and <a href="https://github.com/alex/django-filter">that</a>

    But also it could include links <a href="http://bitbucket.org/antocuni/pdb">to the bitbucked</a>
    To some <a href="https://raw.github.com/tony/tmuxp/master/doc/_static/tmuxp-dev-screenshot.png">raw materials</a>.
    And raw <a href="http://bitbucket.org/antocuni/pdb/raw/0c86c93cee41/screenshot.png">at bitbucket</a>.
    """
    with mock.patch('allmychanges.utils.requests') as requests:
        response = mock.Mock()
        response.content = content
        requests.get.return_value = response
        urls = guess_source('python', 'test')

        eq_(['https://github.com/alex/django-filter',
             'https://bitbucket.org/antocuni/pdb',
             'https://github.com/tony/tmuxp'],
            urls)



def test_filling_missing_dates_when_there_arent_any_dates():
    from datetime import date
    from datetime import timedelta
    today = date.today()
    month = timedelta(30)
    
    item = lambda dt: dict(date=dt)
    eq_([item(today - month), item(today - month), item(today)],
        fill_missing_dates([{}, {}, {}]))


def test_filling_missing_dates_when_there_are_gaps_between():
    from datetime import date
    from datetime import timedelta
    today = date.today()
    month = timedelta(30)
    
    item = lambda dt: dict(date=dt)
    first_date = today - timedelta(7)
    last_date = today - 2 * month
    
    eq_([item(last_date),
         item(last_date),
         item(first_date),
         item(first_date),
         item(today)],
        
        fill_missing_dates([ 
            {}, # 0.1.0
            item(last_date), # 0.2.0
            {}, # 0.2.1
            item(first_date), # 0.3.0
            {}, # 0.4.0
        ]))


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
        response = self.cl.post(url, dict(timezone='Europe/Moscow'))
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
