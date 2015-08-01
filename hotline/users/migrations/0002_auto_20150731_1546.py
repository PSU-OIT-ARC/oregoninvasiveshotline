# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='biography',
            field=models.TextField(default=None),
        ),
        migrations.AddField(
            model_name='user',
            name='photo',
            field=models.ImageField(default=None, upload_to=''),
        ),
        migrations.AlterField(
            model_name='user',
            name='affiliations',
            field=models.TextField(default=None),
        ),
    ]
