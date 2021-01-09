# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counties', '0001_initial'),
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='county',
            field=models.ForeignKey(null=True, to='counties.County', on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
