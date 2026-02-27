# settings.py (VERSÃO FINAL E CORRIGIDA)

from pathlib import Path
import os
from decouple import AutoConfig # Usaremos decouple para segredos

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Força leitura do .env da pasta do projeto (evita captar .env de outros caminhos)
config = AutoConfig(search_path=BASE_DIR)

SECRET_KEY = config('SECRET_KEY')

# Configurações por ambiente
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='ifmaker.cba.ifmt.edu.br,127.0.0.1,localhost, 200.129.251.103, 10.1.149.18').split(',')
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://ifmaker.cba.ifmt.edu.br,http://127.0.0.1,http://localhost,'
).split(',')

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
    'Controle_ar',
    'Email_notificacoes',
    'widget_tweaks',
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

# CORRIGIDO: Configuração para o banco de dados PostgreSQL
if DEBUG:
    # Fallback simples para desenvolvimento local sem Postgres
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    if DEBUG:
        # Fallback para ambiente local: usar SQLite se não houver Postgres configurado
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('DB_NAME', default='fablab_db'),
                'USER': config('DB_USER', default='fablab_user'),
                'PASSWORD': config('DB_PASSWORD', default='fablab_pass'),
                'HOST': config('DB_HOST', default='db'),
                'PORT': config('DB_PORT', default='5432'),
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
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='FabLab <ifmtmaker.fablab.cba@gmail.com>')

# Configuração de Logging para vermos os erros
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'error.log'),
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'error_file'],
        'level': 'INFO', # Mostra mensagens informativas, de aviso e de erro
    },
}

# Regras de segurança para produção
if not DEBUG:
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # USE_X_FORWARDED_HOST = True
    # SECURE_SSL_REDIRECT = True  # COMENTADO TEMPORARIAMENTE PARA TESTE
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 31536000 # COMENTADO TEMPORARIAMENTE PARA TESTE
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True # COMENTADO TEMPORARIAMENTE PARA TESTE
    # SECURE_HSTS_PRELOAD = True # COMENTADO TEMPORARIAMENTE PARA TESTE