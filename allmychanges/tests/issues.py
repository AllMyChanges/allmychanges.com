from nose.tools import eq_
from django.utils import timezone
from allmychanges.changelog_updater import update_changelog_from_raw_data2
from allmychanges.models import Changelog
from allmychanges.env import Environment

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
    data = [v(version='0.2.0', content=[]),
            v(version='0.3.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])


def test_add_issue_if_we_found_more_than_one_new_version():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # we already know about one version
    changelog.versions.create(
        number='0.2.0', code_version='v2')

    # but we are unaware about 0.3.0 and 0.4.0
    data = [v(version='0.2.0', content=[]),
            v(version='0.3.0', content=[]),
            v(version='0.4.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    eq_(['too-many-new-versions'],
        [i.type for i in changelog.issues.all()])


def test_add_issue_only_if_there_are_already_some_versions():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # there isnt' any versions in the changelog
    # but we found three new versions
    # possible, this package was added few seconds ago
    data = [v(version='0.2.0', content=[]),
            v(version='0.3.0', content=[]),
            v(version='0.4.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    # there isn't any versions in the changelog
    # so we shouldn't create an issue
    eq_([],
        [i.type for i in changelog.issues.all()])


def test_add_issue_if_subsequent_discovery_found_less_versions():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    # first discovery found 3 versions
    data = [v(version='0.2.0', content=[]),
            v(version='0.3.0', content=[]),
            v(version='0.4.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    eq_([],
        [i.type for i in changelog.issues.all()])


    # second discovery found only one versions
    data = [v(version='0.2.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    eq_(['lesser-version-count'],
        [i.type for i in changelog.issues.all()])
    eq_('This time we didn\'t discover 0.3.0, 0.4.0 versions',
        changelog.issues.latest('id').comment)


    # now we check that subsequent discoveries don't
    # create new issues until we resolve this one
    data = [v(version='0.2.0', content=[])]

    update_changelog_from_raw_data2(changelog, data)

    eq_(['lesser-version-count'],
        [i.type for i in changelog.issues.all()])


    # but if we resolve the issue, then
    # it could appear again
    changelog.resolve_issues(type='lesser-version-count')

    update_changelog_from_raw_data2(changelog, data)

    eq_([('lesser-version-count', timezone.now().date()),
         ('lesser-version-count', None)],
        [(i.type, i.resolved_at.date() if i.resolved_at else None)
         for i in changelog.issues.all()])
