# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(unique=True, max_length=255)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('prefix', models.CharField(max_length=255)),
                ('suffix', models.CharField(max_length=255)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True, help_text='Inactive users cannot login')),
                ('is_manager', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('affiliations', models.TextField()),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
                'db_table': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
