# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_changelog_field_for_tags(apps, schema_editor):
    Tag = apps.get_model('allmychanges', 'Tag')

    for tag in Tag.objects.filter(changelog=None):
        tag.changelog = tag.version.changelog
        tag.save()


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0012_auto_20160425_0542'),
    ]

    operations = [
        migrations.RunPython(update_changelog_field_for_tags)
    ]
