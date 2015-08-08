# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('species', '0003_auto_20150727_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='severity',
            name='color',
            field=models.CharField(help_text="An HTML color of the form '#rrggbb'", max_length=7, default=''),
            preserve_default=False,
        ),
    ]
