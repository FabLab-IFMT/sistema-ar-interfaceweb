# Generated by Django 5.0.1 on 2025-03-24 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0005_alter_action_options_action_ip_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='author',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
