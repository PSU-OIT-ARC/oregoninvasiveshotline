# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['pk']},
        ),
        migrations.AlterField(
            model_name='image',
            name='name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='image',
            name='visibility',
            field=models.IntegerField(default=1, choices=[(0, 'Private - only managers and invited experts can see'), (1, 'Protected - only managers, invited experts and the report submitter can see'), (2, 'Public - everyone can see (when this report is made public)')]),
        ),
    ]
