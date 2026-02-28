from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_role_and_user_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='email_verified',
            field=models.BooleanField(default=True, help_text='Indica se o email foi confirmado'),
        ),
        migrations.CreateModel(
            name='ProjectistRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivation', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projetista_decisions', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projetista_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitação de Projetista',
                'verbose_name_plural': 'Solicitações de Projetista',
                'ordering': ['-created_at'],
            },
        ),
    ]
