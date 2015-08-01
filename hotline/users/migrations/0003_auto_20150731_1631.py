# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20150731_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='affiliations',
            field=models.TextField(null=True, blank=True, default=None),
        ),
        migrations.AlterField(
            model_name='user',
            name='biography',
            field=models.TextField(null=True, blank=True, default=None),
        ),
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.ImageField(null=True, blank=True, upload_to='', default=None),
        ),
    ]
