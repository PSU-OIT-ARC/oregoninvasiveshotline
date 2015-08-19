# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='affiliations',
            field=models.TextField(default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='biography',
            field=models.TextField(default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.ImageField(default=None, blank=True, upload_to=''),
        ),
    ]
