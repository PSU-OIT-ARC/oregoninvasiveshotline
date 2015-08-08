# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('species', '0004_auto_20150728_0903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.ImageField(help_text='\n        It is expected that you got the icon from http://mapicons.mapsmarker.com\n        and they have a transparent background, and a white foreground\n    ', null=True, blank=True, upload_to='icons'),
        ),
    ]
