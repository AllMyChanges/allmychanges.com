from nose.tools import eq_
from allmychanges.models import Changelog
from .utils import create_user
from allmychanges.changelog_updater import (
    update_changelog)

def test_update_package_using_full_pipeline():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test+samples/very-simple.md')
    art.track(changelog)

    update_changelog(changelog)

    versions = list(changelog.versions.filter(code_version='v2'))
    eq_(2, len(versions))
    eq_('<span class="changelog-item-type changelog-item-type_fix">fix</span>Some bugfix.',
        versions[0].sections.all()[0].items.all()[0].text)
    eq_('<span class="changelog-item-type changelog-item-type_new">new</span>Initial release.',
        versions[1].sections.all()[0].items.all()[0].text)
