# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('comment_id', models.AutoField(primary_key=True, serialize=False)),
                ('body', models.TextField()),
                ('created_on', models.DateField(auto_now_add=True)),
                ('edited_on', models.DateField(auto_now=True)),
                ('visibility', models.IntegerField(default=0, help_text='Controls who can see this comment', choices=[(0, 'Private - only managers and invited experts can see'), (1, 'Protected - only managers, invited experts and the report submitter can see'), (2, 'Public - everyone can see (when this report is made public)')])),
                ('created_by', models.ForeignKey(to='users.User')),
                ('report', models.ForeignKey(to='reports.Report')),
            ],
            options={
                'db_table': 'comment',
            },
        ),
    ]
