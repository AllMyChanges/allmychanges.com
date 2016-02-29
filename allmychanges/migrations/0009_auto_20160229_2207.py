# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0008_auto_20160228_0808'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='resolved_by',
            field=models.ForeignKey(related_name='resolved_issues', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='feeditem',
            name='version',
            field=models.ForeignKey(related_name='feed_items', to='allmychanges.Version'),
        ),
    ]
