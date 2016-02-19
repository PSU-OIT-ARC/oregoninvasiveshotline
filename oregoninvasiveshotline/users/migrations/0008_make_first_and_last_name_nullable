from django.db import migrations, models


def empty_strings_to_null(apps, schema_editor):
    model = apps.get_model('users', 'User')
    model.objects.filter(first_name='').update(first_name=None)
    model.objects.filter(last_name='').update(last_name=None)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_fix_default_ordering_of_user_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(null=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(null=True, max_length=255),
        ),

        migrations.RunPython(empty_strings_to_null),
    ]
