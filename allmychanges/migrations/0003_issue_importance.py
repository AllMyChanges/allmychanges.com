# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0002_auto_20160216_0839'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='importance',
            field=models.IntegerField(default=0, db_index=True, blank=True),
        ),
    ]
