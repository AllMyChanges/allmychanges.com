# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_changelog_field_for_tags(apps, schema_editor):
    Tag = apps.get_model('allmychanges', 'Tag')

    for tag in Tag.objects.filter(changelog=None):
        changelog = tag.version.changelog

        already_exists = Tag.objects.filter(
            changelog=changelog,
            user=tag.user,
            name=tag.name).count()

        if already_exists:
            Tag.objects.filter(pk=tag.pk).delete()
        else:
            tag.changelog = changelog
            tag.save()


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0013_auto_20160426_0850'),
    ]

    operations = [
        migrations.RunPython(update_changelog_field_for_tags)
    ]
