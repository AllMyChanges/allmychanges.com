# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0007_auto_20160227_1155'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='feed_sent_id',
            field=models.IntegerField(default=0, help_text=b'Keeps position in feed items already sent in digest emails'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_digest_sent_at',
            field=models.DateTimeField(help_text=b'Date when last email digest was sent', null=True, blank=True),
        ),
    ]
