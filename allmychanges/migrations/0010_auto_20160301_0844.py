# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0009_auto_20160229_2207'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('user', models.ForeignKey(related_name='tags', to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(related_name='tags', to='allmychanges.Version')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('version', 'user', 'name')]),
        ),
    ]
