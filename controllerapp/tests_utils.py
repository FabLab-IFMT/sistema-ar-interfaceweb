"""Utilitários compartilhados entre os testes do projeto."""
import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def make_image_file(filename='test.jpg', fmt='JPEG', mode='RGB', size=(100, 100)):
    """Retorna um SimpleUploadedFile com uma imagem sintética."""
    color = (255, 0, 0, 128) if 'A' in mode else (255, 0, 0)
    img = Image.new(mode, size, color=color)
    buf = io.BytesIO()
    save_fmt = 'PNG' if 'A' in mode else fmt
    img.save(buf, format=save_fmt)
    buf.seek(0)
    content_type = f'image/{"jpeg" if fmt.upper() == "JPEG" else fmt.lower()}'
    return SimpleUploadedFile(filename, buf.read(), content_type=content_type)


def create_user(matricula='12345678901', password='senha@123', **kwargs):
    defaults = {
        'first_name': 'Joao',
        'last_name': 'Teste',
        'email': f'{matricula}@test.com',
    }
    defaults.update(kwargs)
    user = User(id=matricula, **defaults)
    user.set_password(password)
    user.save()
    return user


def create_staff(matricula='88888888888', password='staff@123', **kwargs):
    defaults = {
        'is_staff': True,
        'email': f'{matricula}@test.com',
        'first_name': 'Staff',
        'last_name': 'User',
    }
    defaults.update(kwargs)
    return create_user(matricula, password, **defaults)


def create_superuser(matricula='99999999999', password='admin@123', **kwargs):
    defaults = {
        'is_staff': True,
        'is_superuser': True,
        'email': f'{matricula}@test.com',
        'first_name': 'Admin',
        'last_name': 'Super',
    }
    defaults.update(kwargs)
    return create_user(matricula, password, **defaults)


def auth_client(user):
    """Retorna um APIClient pré-autenticado como `user`."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client
