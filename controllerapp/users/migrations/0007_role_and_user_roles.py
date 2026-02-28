from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_registrationrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('is_staff_equivalent', models.BooleanField(default=False, help_text='Se marcado, o usuário recebe permissões de staff ao ter este cargo.')),
            ],
            options={
                'verbose_name': 'Cargo',
                'verbose_name_plural': 'Cargos',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='customuser',
            name='roles',
            field=models.ManyToManyField(blank=True, related_name='users', to='users.role'),
        ),
    ]
