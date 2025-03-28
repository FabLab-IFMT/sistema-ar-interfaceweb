# Generated by Django 5.0.1 on 2025-02-27 15:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Controle_ar', '0002_carouselimage_description_carouselimage_link_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ar_condicionado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50)),
                ('tag', models.CharField(max_length=50, unique=True)),
                ('estado', models.BooleanField(default=False)),
                ('temperatura', models.IntegerField(default=20)),
                ('modo', models.CharField(default='cold', max_length=20)),
                ('velocidade', models.IntegerField(default=1)),
                ('swing', models.BooleanField(default=False)),
                ('ultima_alteracao', models.DateTimeField(auto_now=True)),
                ('online', models.BooleanField(default=True)),
                ('ultimo_ping', models.DateTimeField(blank=True, null=True)),
                ('consumo_atual', models.FloatField(default=0.0, help_text='Consumo atual em kW/h')),
                ('temperatura_ambiente', models.FloatField(blank=True, help_text='Temperatura ambiente em °C', null=True)),
            ],
            options={
                'verbose_name': 'Ar Condicionado',
                'verbose_name_plural': 'Ar Condicionados',
            },
        ),
        migrations.CreateModel(
            name='Comando_ar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comando', models.CharField(max_length=100)),
                ('executado', models.BooleanField(default=False)),
                ('data_hora', models.DateTimeField(auto_now_add=True)),
                ('ar_condicionado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Controle_ar.ar_condicionado')),
            ],
            options={
                'verbose_name': 'Comando de Ar',
                'verbose_name_plural': 'Comandos de Ar',
            },
        ),
        migrations.CreateModel(
            name='LogOperacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operacao', models.CharField(max_length=100)),
                ('usuario', models.CharField(max_length=100)),
                ('data_hora', models.DateTimeField(auto_now_add=True)),
                ('ar_condicionado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Controle_ar.ar_condicionado')),
            ],
            options={
                'verbose_name': 'Log de Operação',
                'verbose_name_plural': 'Logs de Operação',
            },
        ),
    ]
