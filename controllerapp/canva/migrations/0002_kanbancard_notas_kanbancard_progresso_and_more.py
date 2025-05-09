# Generated by Django 5.0.1 on 2025-05-03 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('canva', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='kanbancard',
            name='notas',
            field=models.TextField(blank=True, help_text='Anotações rápidas sobre a tarefa'),
        ),
        migrations.AddField(
            model_name='kanbancard',
            name='progresso',
            field=models.PositiveSmallIntegerField(default=0, help_text='Progresso em percentual (0-100)'),
        ),
        migrations.AddField(
            model_name='kanbancard',
            name='tempo_trabalhado',
            field=models.PositiveIntegerField(default=0, help_text='Tempo trabalhado em segundos'),
        ),
    ]
