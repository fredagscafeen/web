from fredagscafeen.settings.base import *

DEBUG = False

SELF_URL = 'http://fredagscafeen.dk/'
ALLOWED_HOSTS = [
    '*'
]

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'datcafe@gmail.com'
EMAIL_HOST_PASSWORD = 'Fad!Oel!'
EMAIL_USE_SSL = True
EMAIL_PORT = 465

import dj_database_url

DATABASES = {'default': dj_database_url.config()}

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
