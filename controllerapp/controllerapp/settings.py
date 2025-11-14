# settings.py (VERSÃO FINAL E CORRIGIDA)

from pathlib import Path
import os
from decouple import config  # Usaremos decouple para segredos

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Usa valor do .env ou, em último caso, uma chave fixa já existente no projeto.
# Substitua esta string pela SECRET_KEY antiga se você tiver.
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-substitua-por-uma-chave-realmente-secreta'
)

# Em produção, DEBUG é sempre False; em dev pode ser controlado via .env
DEBUG = config('DEBUG', default=False, cast=bool)

# CORRIGIDO: Sem https:// no ALLOWED_HOSTS
ALLOWED_HOSTS = ['ifmaker.cba.ifmt.edu.br', '127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['https://ifmaker.cba.ifmt.edu.br']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'repositorio',
    'projetos',
    'logs',
    'options',
    'users',
    'gestao',
    'acesso_e_ponto',
    'canva',
    'inventario',
    'gestao_projetos',
    'Controle_ar',
    'Email_notificacoes',
    'todo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware de manutenção desativado
    # 'controllerapp.middleware.MaintenanceModeMiddleware', 
    'logs.middleware.LogMiddleware',
]

ROOT_URLCONF = 'controllerapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'logs.context_processors.pending_events_count',
                'users.context_processors.registration_requests_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'controllerapp.wsgi.application'

# Banco de dados para desenvolvimento (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation (sem alterações)
AUTH_PASSWORD_VALIDATORS = [
    # ...
]

# Internationalization
LANGUAGE_CODE = 'pt-br'

# CORRIGIDO: Apenas uma definição de fuso horário
TIME_ZONE = 'America/Cuiaba'

USE_I18N = True
USE_TZ = True

# --- Configuração Definitiva de Arquivos Estáticos e de Mídia ---
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Para DESENVOLVIMENTO (runserver com DEBUG=True)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
# Para PRODUÇÃO (collectstatic e Nginx)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR.parent, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = "users.CustomUser"
LOGIN_URL = '/users/login/'

# Configurações de Email (usando decouple)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='FabLab <ifmtmaker.fablab.cba@gmail.com>'
)

# Configuração de Logging para vermos os erros
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Mostra mensagens informativas, de aviso e de erro
    },
}