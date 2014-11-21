# coding: utf-8
import anyjson
from urllib import urlencode
from nose.tools import eq_
from allmychanges.models import Changelog, Preview
from django.test import Client
from django.core.urlresolvers import reverse
from allmychanges.tasks import _task_log, update_preview_task
from .utils import refresh


def test_preview():
    cl = Client()
    eq_(0, Preview.objects.count())
    eq_(0, Changelog.objects.count())

    # when user opens add-new page, a new changelog and preview
    # are created
    source = 'test+samples/very-simple.md'
    cl.get(reverse('add-new') + '?' + urlencode(dict(url=source)))
    eq_(1, Changelog.objects.count())
    eq_(1, Preview.objects.count())

    preview = Preview.objects.all()[0]
    eq_(None, preview.user)
    assert preview.light_user != None

    eq_([('update_preview_task', (1,), {})], _task_log)


    preview_url = reverse('preview', kwargs=dict(pk=preview.pk))
    response = cl.get(preview_url)
    eq_(200, response.status_code)

    assert 'Some bugfix.' in response.content
    assert 'Initial release.' in response.content

    # при этом, у объекта preview должны быть версии, а у changelog нет
    changelog = Changelog.objects.all()[0]
    eq_(0, changelog.versions.count())
    eq_(2, preview.versions.count())


    # теперь обновим preview на несуществующий источник
    response = cl.post(preview_url,
                       data=anyjson.serialize(dict(source='another source',
                                                   ignore_list='NEWS',
                                                   search_list='docs')),
                       content_type='application/json')
    eq_(200, response.status_code)
    preview = refresh(preview)
    eq_('another source', preview.source)
    eq_('NEWS', preview.ignore_list)
    eq_('docs', preview.check_list)

    # and another preview task was scheduled
    eq_([('update_preview_task', (1,), {}),
         ('update_preview_task', (1,), {})], _task_log)

    # версии должны были удалиться
    eq_(0, changelog.versions.count())
    eq_(0, preview.versions.count())
    # а само preview перейти в состояние error
    eq_('error', preview.status)




def test_update_package_preview_versions():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test+samples/markdown-release-notes')
    preview = changelog.previews.create(light_user='anonymous',
                                        source=changelog.source)

    preview.schedule_update()

    eq_(0, changelog.versions.filter(preview=None).count())

    def first_item(version):
        return version.sections.all()[0].items.all()[0].text

    def first_items(versions):
        return map(first_item, versions)

    versions = preview.versions.filter(code_version='v2')
    eq_(['<span class="changelog-item-type changelog-item-type_new">new</span>Some crap',
         '<span class="changelog-item-type changelog-item-type_fix">fix</span>Some bugfix.',
         '<span class="changelog-item-type changelog-item-type_new">new</span>Initial release.'],
        first_items(versions))

    # now we'll check if ignore list works
    preview.set_ignore_list(['docs/unrelated-crap.md'])
    preview.save()
    preview.schedule_update()

    versions = preview.versions.filter(code_version='v2')
    eq_(['<span class="changelog-item-type changelog-item-type_fix">fix</span>Some bugfix.',
         '<span class="changelog-item-type changelog-item-type_new">new</span>Initial release.'],
        first_items(versions))
