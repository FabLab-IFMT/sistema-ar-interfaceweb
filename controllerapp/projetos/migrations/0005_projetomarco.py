from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projetos', '0004_todotask_visivel_para_alter_todotask_usuario_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjetoMarco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200)),
                ('descricao', models.TextField(blank=True)),
                ('data', models.DateField()),
                ('progresso', models.PositiveSmallIntegerField(default=0)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marcos_criados', to=settings.AUTH_USER_MODEL)),
                ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marcos', to='projetos.projeto')),
                ('responsavel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marcos_responsavel', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Marco do Projeto',
                'verbose_name_plural': 'Marcos do Projeto',
                'ordering': ['data', 'ordem', 'id'],
            },
        ),
    ]
