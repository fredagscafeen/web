"""
Django settings for fredagscafeen project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

MAILMAN_URL_BASE = 'http://maillist.au.dk/mailman'
MAILMAN_ALL_LIST = 'datcafe-alle.cs'
MAILMAN_BEST_LIST = 'datcafe-best.cs'

SECRET_ADMIN_KEYS = [
    ('SECRET_KEY', 'Django secret key'),
    ('MAILMAN_ALL_PASSWORD', 'Alle mailinglist admin password'),
    ('MAILMAN_BEST_PASSWORD', 'Best mailinglist admin password'),
    ('EMAIL_HOST_PASSWORD', 'Gmail password'),
    ('DIGITAL_OCEAN_PASSWORD', 'Digital Ocean password'),
    ('RECAPTCHA_PRIVATE_KEY', 'ReCaptcha private key'),
]

# Inject all secret keys
for k, _ in SECRET_ADMIN_KEYS:
    v = os.getenv(k)
    if v != None:
        globals()[k] = v
    else:
        print('WARNING: Missing secret key in env:', k)

# SECURITY WARNING: don't run with debug turned on in production!

# ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'admin_views',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_object_actions',
    'django_extensions',
    'rest_framework.authtoken',
    'bootstrap3',
    'captcha',
    'items',
    'bartenders',
    'rest_framework',
    'web',
    'api',
    'reminder',
    'udlejning',
    'logentry_admin',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'bartenders.auth.BartenderTokenBackend',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    )
}

ROOT_URLCONF = 'fredagscafeen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['web/templates', 'fredagscafeen/templates'],
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

WSGI_APPLICATION = 'fredagscafeen.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'da-DK'

TIME_ZONE = 'Europe/Copenhagen'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Use the new NoCaptcha
NOCAPTCHA = True

# Server admins (get an email when server errors happen)
ADMINS = [
    ('Oskar Haarklou Veileborg', 'oskarv@post.au.dk'),
    ('Jonas Tranberg Sørensen', '201406818@post.au.dk'),
    ('Asger Hautop Drewsen', 'asgerdrewsen@gmail.com'),
]
