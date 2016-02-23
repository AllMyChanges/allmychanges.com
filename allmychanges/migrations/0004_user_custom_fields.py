# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0003_issue_importance'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='custom_fields',
            field=jsonfield.fields.JSONField(default={}, help_text=b'Custom fields such like "Location" or "SecondEmail".', blank=True),
        ),
    ]
