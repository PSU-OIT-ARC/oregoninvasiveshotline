# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('category_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'category',
            },
        ),
        migrations.CreateModel(
            name='Severity',
            fields=[
                ('severity_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'severity',
            },
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('species_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('scientific_name', models.CharField(max_length=255)),
                ('remedy', models.TextField()),
                ('resources', models.TextField()),
                ('confidential', models.BooleanField(default=False, help_text='\n        A species can be marked as confidential if making a report about it public would cause harm\n    ')),
                ('category', models.ForeignKey(to='species.Category')),
                ('severity', models.ForeignKey(to='species.Severity')),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'species',
            },
        ),
    ]
