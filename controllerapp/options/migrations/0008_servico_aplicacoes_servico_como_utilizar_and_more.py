# Generated by Django 5.0.1 on 2025-05-15 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0007_rename_descrição_do_material_material_descricao_do_material_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='servico',
            name='aplicacoes',
            field=models.TextField(blank=True, help_text='Aplicações possíveis para este serviço', null=True),
        ),
        migrations.AddField(
            model_name='servico',
            name='como_utilizar',
            field=models.TextField(blank=True, help_text='Instruções personalizadas de como utilizar este serviço', null=True),
        ),
        migrations.AddField(
            model_name='servico',
            name='especificacoes',
            field=models.TextField(blank=True, help_text='Especificações técnicas do serviço/equipamento', null=True),
        ),
    ]
