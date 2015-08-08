# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_auto_20150805_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernotificationquery',
            name='query',
            field=models.TextField(help_text='\n        This is a a string for a QueryDict of the GET parameters to pass to the\n        ReportSearchForm that match reports the user should be notified about\n    '),
        ),
    ]
