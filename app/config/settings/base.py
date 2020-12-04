import os
import pathlib
from datetime import timedelta

from .logging_ import LOGGING, LOGGING_DIR

# Basic django settings
BASE_DIR = pathlib.Path(__file__).parents[2]

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(' ')

SECRET_KEY = os.environ.get('SECRET_KEY')

ROOT_URLCONF = 'config.urls'

AUTH_USER_MODEL = 'accounts.User'

WSGI_APPLICATION = 'wsgi.application'

# apps
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'imagekit',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'django_celery_beat',
    
    'apps.accounts.apps.AccountsConfig',
    'apps.swagger_projects.apps.SwaggerProjectsConfig',
]

# middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication and Authorization related settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

COMPANY_INVITATION_TOKEN_EXPIRES_IN_MINUTES = int(os.environ.get(
    'COMPANY_INVITATION_TOKEN_EXPIRES_IN'))

PASSWORD_RESET_TOKEN_EXPIRES_IN_MINUTES = int(os.environ.get(
    'PASSWORD_RESET_TOKEN_EXPIRES_IN'))

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=360),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get(
        'REFRESH_TOKEN_LIFETIME'
    )))
}

# Template related settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# DB related settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('SQL_DATABASE'),
        'USER': os.environ.get('SQL_USER'),
        'PASSWORD': os.environ.get('SQL_PASSWORD'),
        'HOST': os.environ.get('SQL_HOST'),
        'PORT': os.environ.get('SQL_PORT'),
    }
}

# Localization and timezone related settings
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = True

USE_TZ = True

# Email related settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

TEMPLATED_EMAIL_BACKEND = 'templated_email.backends.vanilla_django.TemplateBackend'
TEMPLATED_EMAIL_TEMPLATE_DIR = 'emails/'
TEMPLATED_EMAIL_FILE_EXTENSION = 'html'

# DRF related settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'EXCEPTION_HANDLER': 'shared.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'shared.parsers.ORJSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'shared.renderers.ORJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# VCS integration related settings
VCS_CREDENTIALS = {
    'GITHUB': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
    },
    'BITBUCKET': {
        'client_id': os.environ.get('BITBUCKET_CLIENT_ID'),
        'client_secret': os.environ.get('BITBUCKET_CLIENT_SECRET'),
    },
}

# Static and media files related settings
STATIC_URL = '/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/mediafiles/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# requests lib related settings
REQUESTS_DEFAULT_TIMEOUT_IN_SECONDS = int(os.environ.get(
    'REQUESTS_DEFAULT_TIMEOUT'))

# Celery related settings
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_RESULT_BACKEND = 'rpc://'

BROKER_URL = 'amqp://{}:{}@{}:{}//'.format(
    os.environ.get('BROKER_USER'),
    os.environ.get('BROKER_PASSWORD'),
    os.environ.get('BROKER_HOST'),
    os.environ.get('BROKER_PORT')
)

# Frontend integration related settings
CLIENT_SITE_BASE_URL = os.environ.get('CLIENT_SITE_BASE_URL')
CORS_ORIGIN_WHITELIST = os.environ.get('CORS_ORIGIN_WHITELIST').split(' ')
CORS_ALLOW_CREDENTIALS = True
