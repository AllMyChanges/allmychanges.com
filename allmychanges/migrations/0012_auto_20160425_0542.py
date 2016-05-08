# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0011_auto_20160415_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='changelog',
            field=models.ForeignKey(related_name='tags', blank=True, to='allmychanges.Changelog', null=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='version_number',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tag',
            name='version',
            field=models.ForeignKey(related_name='tags', blank=True, to='allmychanges.Version', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('changelog', 'user', 'name')]),
        ),
    ]
