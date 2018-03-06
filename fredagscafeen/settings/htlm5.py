from fredagscafeen.settings.base import *

DEBUG = False

SELF_URL = 'http://fredagscafeen.dk/'
ALLOWED_HOSTS = [
    '*'
]

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'datcafe@gmail.com'
EMAIL_HOST_PASSWORD = '!Fad!Oel!'
EMAIL_USE_SSL = True
EMAIL_PORT = 465

import dj_database_url

DATABASES = {'default': dj_database_url.config()}

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

RECAPTCHA_PUBLIC_KEY = '6LeyixoUAAAAAFkkXnzfT8932ENQQmD2a2LLs2Bt'
RECAPTCHA_PRIVATE_KEY = '6LeyixoUAAAAAFKIL_ycYN9nzBAB-CTxY4D8Du2q'

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
