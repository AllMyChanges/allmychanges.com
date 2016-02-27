# coding: utf-8
import re

from nose.tools import eq_
from allmychanges.models import Changelog
from .utils import create_user
from allmychanges.changelog_updater import (
    update_preview_or_changelog)
from allmychanges.env import Environment
from allmychanges.parsing.pipeline import parse_html_file


def test_update_package_using_full_pipeline():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/very-simple.md',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    versions = list(changelog.versions.all())
    eq_(2, len(versions))
    eq_('<ul>\n<li>Some bugfix.</li>\n</ul>',
        versions[0].raw_text)
    eq_('<ul>\n<li>Initial release.</li>\n</ul>',
        versions[1].raw_text)

    # TODO: uncomment when I add text processing
    # eq_('<span class="changelog-item-type changelog-item-type_fix">fix</span>Some bugfix.',
    #     versions[0].raw_text)
    # eq_('<span class="changelog-item-type changelog-item-type_new">new</span>Initial release.',
    #     versions[1].raw_text)


def test_html_parser():
    env = Environment(filename='Changelog',
                      content=u"""
<div class="markdown-body">
<h2>
<a id="user-content-v021" class="anchor" href="#v021" aria-hidden="true"><span class="octicon octicon-link"></span></a><sub>v0.2.1</sub>
</h2>

<h4>
<a id="user-content-may-24-2012--diff--docs" class="anchor" href="#may-24-2012--diff--docs" aria-hidden="true"><span class="octicon octicon-link"></span></a><em>May 24, 2012</em> — <a href="https://github.com/lodash/lodash/compare/0.2.0...0.2.1">Diff</a> — <a href="https://github.com/lodash/lodash/blob/0.2.1/doc/README.md">Docs</a>
</h4>

<ul class="task-list">
<li>Adjusted the Lo-Dash export order for r.js</li>
<li>Ensured <code>_.groupBy</code> values are added to own, not inherited, properties</li>
<li>Made <code>_.bind</code> follow ES5 spec to support a popular Backbone.js pattern</li>
<li>Removed the alias <code>_.intersect</code>
</li>
<li>Simplified <code>_.bind</code>, <code>_.flatten</code>, <code>_.groupBy</code>, <code>_.max</code>, &amp; <code>_.min</code>
</li>
</ul>

<h2>
<a id="user-content-v010" class="anchor" href="#v010" aria-hidden="true"><span class="octicon octicon-link"></span></a><sub>v0.1.0</sub>
</h2>

<h4>
<a id="user-content-apr-23-2012--docs" class="anchor" href="#apr-23-2012--docs" aria-hidden="true"><span class="octicon octicon-link"></span></a><em>Apr. 23, 2012</em> — <a href="https://github.com/lodash/lodash/blob/0.1.0/doc/README.md">Docs</a>
</h4>

<ul class="task-list">
<li>Initial release</li>
</ul>

    </div>
                      """)

    sections = list(parse_html_file(env))
    eq_(5, len(sections))

    eq_(['Changelog',
         'v0.2.1',
         u'May 24, 2012 \u2014 Diff \u2014 Docs',
         'v0.1.0',
         u'Apr. 23, 2012 \u2014 Docs'],
        [s.title for s in sections])

    eq_('<h4>\n<a id="user-content-apr-23-2012--docs" class="anchor" href="#apr-23-2012--docs" aria-hidden="true"><span class="octicon octicon-link"></span></a><em>Apr. 23, 2012</em> &#8212; <a href="https://github.com/lodash/lodash/blob/0.1.0/doc/README.md">Docs</a>\n</h4>\n\n<ul class="task-list">\n<li>Initial release</li>\n</ul>',
        sections[3].content)


def test_html_parser_makes_hierarchy():
    env = Environment(filename='Changelog',
                      content=u"""
<h1>Level 1.1</h1>
  <h2>Level 2.1</h2>
    <h3>Level 3.1</h3>
    <p>Bottom level description</p>
  <h2>Level 2.2</h2>
<h1>Level 1.2</h1>
""")

    sections = list(parse_html_file(env))

    eq_(6, len(sections))
    s0, s1, s2, s3, s4, s5 = sections

    eq_('Level 2.1', s2.title)
    assert 'Level 3.1' in s2.content
    assert 'Level 2.2' not in s2.content

    assert s0.is_parent_for(s1)
    assert s1.is_parent_for(s2)
    assert s0.is_parent_for(s2)

    eq_('Level 3.1', s3.title)
    eq_('<p>Bottom level description</p>', s3.content)
    assert s2.is_parent_for(s3)
    assert s1.is_parent_for(s2)
    assert s0.is_parent_for(s2)


def test_exclude_version_if_it_includes_few_other_versions():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/celery/1',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    # there shouldn't be 3.1 version because it is just number from a filename
    eq_(0, changelog.versions.filter(number='3.1').count())



def test_exclude_version_if_it_included_in_the_version_with_same_number_and_bigger_content():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/celery/2',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    # there should be 3.1 version and it's content should include entire file
    # with a header because there aren't any versions there yet
    eq_(1, changelog.versions.filter(number='3.1').count())
    eq_(1, changelog.versions.all().count())

    version = changelog.versions.all()[0]
    eq_(u'<h1>3.1<a href="#id1" title="Permalink to this headline">\xb6</a></h1><p>Version description.</p>',
        re.sub(ur' +', u' ',
               re.sub(ur'[\n ]+\n *|\n|<div>|</div>', u'', version.processed_text)).strip())


def test_exclude_outer_version_if_it_includes_a_single_version_which_is_subversion():
    # this is the case when 3.1 version includes one 3.1.0 version
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/celery/3',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    # there should be 3.1.0 version only because now it is only version in a 3.1.rst file
    # with a header because there aren't any versions there yet
    eq_(1, changelog.versions.filter(number='3.1.0').count())
    eq_(1, changelog.versions.all().count())

    version = changelog.versions.all()[0]
    eq_(u'<p>Version description.</p>', version.raw_text)


def test_exclude_inner_version_if_it_is_included_into_an_outer_version_with_differ_number():
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/celery/4',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    # there should be only a 3.1.0 because it includes 3.1.1
    eq_(1, changelog.versions.all().count())
    eq_(1, changelog.versions.filter(number='3.1.0').count())


# def test_exclude_inner_version_if_it_is_greater_than_outer():
#     art = create_user('art')
#     changelog = Changelog.objects.create(
#         namespace='python',
#         name='pip',
#         source='samples/celery/5',
#         downloader='fake')
#     art.track(changelog)

#     update_preview_or_changelog(changelog)

#     # there should be 1.3.0
#     # with a header because there aren't any versions there yet
#     eq_(1, changelog.versions.all().count())
#     eq_(1, changelog.versions.filter(number='1.3.0').count())


def test_not_exclude_two_versions_with_same_content():
    # sometimes there may be a bugfix, which is backported
    # to a few older versions. In this case these versions has the same
    # content an none of them should be excluded
    art = create_user('art')
    changelog = Changelog.objects.create(
        namespace='python',
        name='pip',
        source='samples/express.js',
        downloader='fake')
    art.track(changelog)

    update_preview_or_changelog(changelog)

    # there should be 4.9.3 and 3.17.3 with same content
    eq_(1, changelog.versions.filter(number='3.17.3').count())
    eq_(1, changelog.versions.filter(number='4.9.3').count())


def test_environment_parent():
    parent = Environment(name='parent')
    child = parent.push(name='child')
    unrelated = Environment(name='unrelated')

    eq_(True, parent.is_parent_for(child))
    eq_(False, child.is_parent_for(parent))
    eq_(False, parent.is_parent_for(unrelated))
