# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernotificationquery',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 8, 5, 16, 32, 2, 399731, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usernotificationquery',
            name='name',
            field=models.CharField(verbose_name='\n        To make it easier to review your subscriptions, give the search you\n        just performed a name. For example "Aquatic plants in Multnomah county"\n    ', default='', max_length=255),
            preserve_default=False,
        ),
    ]
