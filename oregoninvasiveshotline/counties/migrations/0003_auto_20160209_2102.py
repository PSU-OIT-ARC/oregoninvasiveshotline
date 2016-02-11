from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counties', '0002_auto_20150804_1609'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='county',
            options={'ordering': ['state', 'name']},
        ),
    ]
