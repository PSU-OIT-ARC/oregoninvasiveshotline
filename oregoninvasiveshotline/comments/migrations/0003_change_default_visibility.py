# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0002_auto_20150813_0849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='visibility',
            field=models.IntegerField(choices=[(0, 'Private - only managers and invited experts can see'), (1, 'Protected - only managers, invited experts and the report submitter can see'), (2, 'Public - everyone can see (when this report is made public)')], help_text='Controls who can see this comment', default=1),
        ),
    ]
