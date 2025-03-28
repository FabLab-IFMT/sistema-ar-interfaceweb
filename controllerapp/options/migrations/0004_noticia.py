# Generated by Django 5.0.1 on 2025-03-23 05:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0003_categoriaservico_servico_projetoexemplo_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Noticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('slug', models.SlugField(help_text='URL amigável baseada no título', max_length=200, unique=True)),
                ('resumo', models.TextField(help_text='Resumo curto da notícia (exibido na listagem)')),
                ('conteudo', models.TextField(help_text='Conteúdo completo da notícia')),
                ('imagem', models.ImageField(help_text='Imagem principal da notícia', upload_to='noticias/')),
                ('data_publicacao', models.DateTimeField(auto_now_add=True)),
                ('data_atualizacao', models.DateTimeField(auto_now=True)),
                ('publicado', models.BooleanField(default=True, help_text='Se marcado, a notícia será visível no site')),
                ('mostrar_na_home', models.BooleanField(default=False, help_text='Se marcado, a notícia será exibida na página inicial')),
                ('destaque', models.BooleanField(default=False, help_text='Se marcado, receberá destaque visual')),
                ('autor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='noticias', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notícia',
                'verbose_name_plural': 'Notícias',
                'ordering': ['-data_publicacao'],
            },
        ),
    ]
