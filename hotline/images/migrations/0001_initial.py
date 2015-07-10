# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
        ('reports', '0001_initial'),
        ('users', '0001_initial'),
        ('species', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('image_id', models.AutoField(primary_key=True, serialize=False)),
                ('image', models.ImageField(upload_to='images')),
                ('name', models.CharField(max_length=255)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('visibility', models.IntegerField(default=1, choices=[(0, 'Private'), (1, 'Protected'), (2, 'Public')])),
                ('comment', models.ForeignKey(default=None, null=True, to='comments.Comment')),
                ('created_by', models.ForeignKey(to='users.User')),
                ('report', models.ForeignKey(default=None, null=True, to='reports.Report')),
                ('species', models.ForeignKey(default=None, null=True, to='species.Species')),
            ],
            options={
                'db_table': 'image',
            },
        ),
    ]
