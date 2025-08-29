from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-q25vadyhqou5z75*^oc#ln6g04f&+t6w@7&2!m$@dr^$h_ch!2'

#################################################################
# SECURITY WARNING: don't run with debug turned on in production!
# Para ver detalhes dos erros durante desenvolvimento, 

# Deixe Debug=True
# Para produção, Debug=False

DEBUG = False

# Ativar modo de manutenção global
MAINTENANCE_MODE = True
#################################################################


ALLOWED_HOSTS = ['https://ifmaker.cba.ifmt.edu.br','ifmaker.cba.ifmt.edu.br', '127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['https://ifmaker.cba.ifmt.edu.br']


#templates de KeyError
TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]


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
    'todo',  # Adicionando o aplicativo de lista de tarefas
]

MIDDLEWARE = [
    # Middleware de manutenção deve vir primeiro para interceptar tudo
    'controllerapp.middleware.MaintenanceModeMiddleware',
    # Middlewares padrão do Django
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'logs.middleware.LogMiddleware',  # Adicionar o middleware de logs
]

ROOT_URLCONF = 'controllerapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'logs.context_processors.pending_events_count',  # Novo context processor
                'users.context_processors.registration_requests_count',  # Adicione o context processor para solicitações de registro
            ],
        },
    },
]

WSGI_APPLICATION = 'controllerapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

TIME_ZONE = 'America/Cuiaba'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- Configuração Definitiva de Arquivos Estáticos e de Mídia ---

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# PARA DESENVOLVIMENTO (runserver com DEBUG=True)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# PARA PRODUÇÃO (collectstatic e Nginx)
# Altere BASE_DIR.parent para apenas BASE_DIR
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR.parent, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "users.CustomUser"

LOGIN_URL = '/users/login/'





#Configurações de EMAIL


# Configuração de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com' 
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ifmtmaker.fablab.cba@gmail.com'
EMAIL_HOST_PASSWORD = 'tgnm eeyu yhyu tycj'  
DEFAULT_FROM_EMAIL = 'FabLab <seu-email@gmail.com>'

# Certifique-se de que o middleware de manutenção esteja funcionando corretamente.
# Lembre-se de testar todas as funcionalidades após as alterações.
# Boa sorte!