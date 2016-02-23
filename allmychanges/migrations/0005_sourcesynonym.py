# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import allmychanges.models


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0004_user_custom_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceSynonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('source', allmychanges.models.URLField(unique=True)),
                ('changelog', models.ForeignKey(related_name='synonyms', to='allmychanges.Changelog')),
            ],
        ),
    ]
