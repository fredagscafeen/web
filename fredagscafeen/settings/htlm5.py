from fredagscafeen.settings.base import *

DEBUG = False

SELF_URL = 'https://fredagscafeen.dk/'
ALLOWED_HOSTS = [
    '*'
]

MAILMAN_MUTABLE = True

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'datcafe@gmail.com'
EMAIL_USE_SSL = True
EMAIL_PORT = 465

import dj_database_url

DATABASES = {'default': dj_database_url.config()}

# Cache (for django-select2)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.getenv('MEMCACHED_URL').replace('memcached://', ''),
    }
}

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

RECAPTCHA_PUBLIC_KEY = '6LcM200UAAAAAIi7AHBSlypIewnLk4Q4BvcC8Z-W'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
