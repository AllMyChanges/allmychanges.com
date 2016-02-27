# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('allmychanges', '0006_auto_20160227_0720'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(to='allmychanges.Version')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='feed_versions',
            field=models.ManyToManyField(related_name='users', through='allmychanges.FeedItem', to='allmychanges.Version'),
        ),
    ]
