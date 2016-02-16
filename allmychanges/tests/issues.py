from nose.tools import eq_
from allmychanges.changelog_updater import update_changelog_from_raw_data3
from allmychanges.models import (
    Changelog,
    User,
    Issue)
from allmychanges.env import Environment
from allmychanges.utils import first
from allmychanges.issues import calculate_issue_importance
from allmychanges.tests.utils import create_user


def v(**kwargs):
    env = Environment()
    env._data.update(kwargs)
    return env


def test_dont_add_issue_if_we_found_only_one_new_version():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # we already know about one version
    changelog.versions.create(
        number='0.2.0', code_version='v2')

    # we discovered a new 0.3.0 version
    # and this is OK.
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])


def test_add_issue_if_we_found_more_than_one_new_version():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # we already know about one version
    changelog.versions.create(
        number='0.2.0', code_version='v2')

    # but we are unaware about 0.3.0 and 0.4.0
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_(['too-many-new-versions'],
        [i.type for i in changelog.issues.all()])
    i = first(changelog.issues)
    eq_(['0.3.0', '0.4.0'],
        i.get_related_versions())


def test_add_issue_only_if_there_are_already_some_versions():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # there isnt' any versions in the changelog
    # but we found three new versions
    # possible, this package was added few seconds ago
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    # there isn't any versions in the changelog
    # so we shouldn't create an issue
    eq_([],
        [i.type for i in changelog.issues.all()])


def test_add_issue_if_subsequent_discovery_found_less_versions():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # first discovery found 3 versions
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])


    # second discovery found only one versions
    data = [v(version='0.2.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_(['lesser-version-count'],
        [i.type for i in changelog.issues.all()])
    eq_('This time we didn\'t discover 0.3.0, 0.4.0 versions',
        changelog.issues.latest('id').comment)


    # now we check that subsequent discoveries don't
    # create new issues until we resolve this one
    data = [v(version='0.2.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_(['lesser-version-count'],
        [i.type for i in changelog.issues.all()])


def test_two_or_more_lesser_versions_issue_could_be_added_for_different_versions_sets():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # first discovery found 3 versions
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])

    # second discovery found only two versions
    data = [v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]
    update_changelog_from_raw_data3(changelog, data)

    # and second time we discovered only 0.4.0
    data = [v(version='0.4.0', content='', processed_content='')]
    update_changelog_from_raw_data3(changelog, data)

    # this should create two issues
    eq_([('lesser-version-count', '0.2.0'),
         ('lesser-version-count', '0.3.0')],
        [(i.type, i.related_versions)
         for i in changelog.issues.all()])


def test_lesser_versions_autoresolve():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # first discovery found 3 versions
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]

    update_changelog_from_raw_data3(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])

    # second discovery found only two versions
    data = [v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]
    update_changelog_from_raw_data3(changelog, data)

    # and now we again discovered all three versions
    data = [v(version='0.2.0', content='', processed_content=''),
            v(version='0.3.0', content='', processed_content=''),
            v(version='0.4.0', content='', processed_content='')]
    update_changelog_from_raw_data3(changelog, data)

    # this should create one issues
    eq_([('lesser-version-count', '0.2.0')],
        [(i.type, i.related_versions)
         for i in changelog.issues.all()])

    issue = changelog.issues.all()[0]
    # and it should be resolved automatically
    assert issue.resolved_at is not None
    eq_('Autoresolved', issue.comments.all()[0].message)


def test_issue_importance():
    # it should be called on issue creation
    c = lambda **kwargs: Issue.objects.create(**kwargs)
    eq_(1, c(changelog=None, user=None).importance)

    user = create_user('art')
    eq_(10, c(changelog=None, user=user).importance)

    # and now we'll test the logic of function it self

    # when no trackers and issue is automatic
    eq_(1, calculate_issue_importance(
        num_trackers=0, user=None, light_user=None))
    # each tracker adds 1 to the final value
    eq_(6, calculate_issue_importance(
        num_trackers=5, user=None, light_user=None))
    # if issue is reported by registered user, then
    # value is multiplied by 10
    eq_(6, calculate_issue_importance(
        num_trackers=5, user=None, light_user=None))
