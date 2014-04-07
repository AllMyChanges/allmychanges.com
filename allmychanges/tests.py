# coding: utf-8
import datetime
import mock
import os.path

from nose.tools import eq_
from django.contrib.auth import get_user_model

from allmychanges.models import Package
from allmychanges.utils import (
    update_changelog_from_raw_data,
    update_changelog,
    fake_downloader,
    guess_source,
    extract_changelog_from_vcs)


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
    
    update_changelog_from_raw_data(package, structure)
    
    eq_(2, package.changelog.versions.count())
    v2 = package.changelog.versions.all()[1]
    eq_('0.2.0', v2.number)
    eq_(['boo fixed', 'baz fixed too'],
        [item.text
         for item in v2.sections.all()[0].items.all()])


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
    
    update_changelog_from_raw_data(package, structure)
    
    v = package.changelog.versions.all()[0]
    date = v.date
    assert date is not None

    with mock.patch('allmychanges.utils.timezone') as timezone:
        timezone.now.return_value = datetime.datetime.now() + datetime.timedelta(10)
        update_changelog_from_raw_data(package, structure)
        
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
    
    update_changelog_from_raw_data(package, structure)
    
    v = package.changelog.versions.all()[0]
    date = v.date
    assert date is not None
    
    new_date = datetime.date(2013, 3, 27)
    structure[0]['date'] = new_date
    update_changelog_from_raw_data(package, structure)
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
        eq_("""0.1.0
======

  * Initial release.
""", content)



def test_update_package_using_full_pipeline():
    art = create_user('art')
    package = Package.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md',
        user=art)
    
    update_changelog(package)
    eq_(1, package.changelog.versions.count())
    eq_('Initial release.', package.changelog.versions.all()[0].sections.all()[0].items.all()[0].text)


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
                                  'Second unreleased feature']}]}],
        
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
