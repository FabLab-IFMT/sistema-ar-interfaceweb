# Generated by Django 5.0.1 on 2025-02-10 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Nome_do_meterial', models.CharField(max_length=100)),
                ('imagem_do_material', models.ImageField(upload_to='materials/')),
                ('descrição_do_material', models.TextField()),
            ],
        ),
    ]
