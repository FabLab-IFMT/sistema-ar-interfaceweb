from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_email_verified_and_projectistrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='users/profile/'),
        ),
    ]
