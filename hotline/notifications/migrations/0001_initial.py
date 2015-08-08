# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_report_county'),
        ('users', '0002_auto_20150730_1458'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('notification_id', models.AutoField(serialize=False, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('report', models.ForeignKey(to='reports.Report')),
                ('user', models.ForeignKey(to='users.User')),
            ],
            options={
                'db_table': 'notification',
            },
        ),
        migrations.CreateModel(
            name='UserNotificationQuery',
            fields=[
                ('user_notification_query_id', models.AutoField(serialize=False, primary_key=True)),
                ('query', models.TextField(help_text='A JSON encoded set of POST parameters to pass to the ReportSearchForm that match reports the user should be notified about')),
                ('user', models.ForeignKey(to='users.User')),
            ],
            options={
                'db_table': 'user_notification_query',
            },
        ),
    ]
