# Generated by Django 2.1.5 on 2020-02-29 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WP', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='repair_parts',
            name='date',
            field=models.DateField(),
            preserve_default=False,
        ),
    ]
