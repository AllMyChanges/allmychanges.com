# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0014_auto_20160426_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 12, 16, 59, 21, 248516, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
