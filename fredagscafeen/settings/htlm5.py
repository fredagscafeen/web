from fredagscafeen.settings.base import *

DEBUG = False

SELF_URL = 'https://fredagscafeen.dk/'
ALLOWED_HOSTS = [
    '*'
]

MAILMAN_MUTABLE = True

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'datcafe@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = True
EMAIL_PORT = 465

import dj_database_url

DATABASES = {'default': dj_database_url.config()}

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

RECAPTCHA_PUBLIC_KEY = '6LcM200UAAAAAIi7AHBSlypIewnLk4Q4BvcC8Z-W'
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

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
