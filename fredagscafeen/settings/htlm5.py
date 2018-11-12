import os
from pathlib import Path
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

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

RECAPTCHA_PUBLIC_KEY = '6LcM200UAAAAAIi7AHBSlypIewnLk4Q4BvcC8Z-W'

# For using latexmk
TEX_BIN = str(list(Path('/app/media/texlive').glob('*/bin/*'))[0])
os.environ['PATH'] = TEX_BIN + ':' + os.environ['PATH']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        # Include the default Django email handler for errors
        # This is what you'd get without configuring logging at all.
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
             # But the emails are plain text by default - HTML is nicer
            'include_html': True,
        },
        # Log to a text file that can be rotated by logrotate
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/app/django.log'
        },
    },
    'loggers': {
        # Again, default Django configuration to email unhandled exceptions
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # Might as well log any errors anywhere else in Django
        'django': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
