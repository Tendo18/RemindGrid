import os
from pathlib import Path
from datetime import timedelta
from decouple import config as env
import dj_database_url
from celery.schedules import crontab


AUTH_USER_MODEL = 'users.User'

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://remind-grid.vercel.app',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'https://remind-grid.vercel.app',
]

CORS_ALLOW_CREDENTIALS = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'django_ratelimit',
    'django_celery_beat',

    'users',
    'subscriptions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'api.wsgi.application'

# Database
# On Heroku, DATABASE_URL is auto-set and takes priority.
# Locally, falls back to your individual DB_* env vars.
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgres://{env('DB_USER', default='')}:{env('DB_PASSWORD', default='')}@{env('DB_HOST', default='localhost')}:{env('DB_PORT', default='5432')}/{env('DB_NAME', default='remindgrid')}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files — whitenoise serves these directly, no separate host needed
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'RemindGrid API',
    'DESCRIPTION': 'Subscription tracking and renewal reminders',
    'VERSION': '1.0.0',
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'remindgridapp@gmail.com'

# Celery / Redis
# IMPORTANT: this was previously always True, meaning tasks never actually
# went through Redis/a worker — they ran synchronously in whatever process
# called them. Now controlled by env var: keep True for quick local testing
# if you want, but it MUST be False in production (Heroku) for the worker
# and beat dynos to do anything at all.
_redis_url = env('REDIS_URL', default=None) or env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = _redis_url
CELERY_RESULT_BACKEND = _redis_url

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Lagos'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Heroku Redis uses rediss:// (TLS) with a self-signed cert — both Celery
# and django-redis need to be told not to verify it, or connections fail.
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': 'CERT_NONE'}
    CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': 'CERT_NONE'}

_redis_cache_url = env('REDIS_URL', default=None) or env('REDIS_CACHE_URL', default='redis://localhost:6379/1')
_cache_options = {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
if _redis_cache_url.startswith('rediss://'):
    _cache_options['CONNECTION_POOL_KWARGS'] = {'ssl_cert_reqs': None}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': _redis_cache_url,
        'OPTIONS': _cache_options,
    }
}

CELERY_BEAT_SCHEDULE = {
    'daily-subscription-maintenance': {
        'task': 'subscriptions.tasks.daily_subscription_maintenance_task',
        'schedule': crontab(hour=6, minute=0),
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Production security settings — only active when DEBUG is False
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')