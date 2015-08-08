# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_report_county'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='edrr_status',
            field=models.IntegerField(default=0, verbose_name='EDDR Status', choices=[(0, ''), (1, 'No Response/Action Required'), (2, 'Local expert notified'), (3, 'Population assessed'), (4, 'Population treated'), (5, 'Ongoing monitoring'), (6, 'Controlled at site')]),
        ),
        migrations.AlterField(
            model_name='report',
            name='has_specimen',
            field=models.BooleanField(default=False, verbose_name='Do you have a physical specimen?'),
        ),
    ]
