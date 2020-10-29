import os
from pathlib import Path

from fredagscafeen.settings.base import *

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False

SELF_URL = "https://fredagscafeen.dk/"
ALLOWED_HOSTS = ["fredagscafeen.dk"]

MEDIA_URL = "https://media.fredagscafeen.dk/"

# Only send session cookie when using https
SESSION_COOKIE_SECURE = True

MAILMAN_MUTABLE = True

EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = "datcafe@gmail.com"
EMAIL_USE_SSL = True
EMAIL_PORT = 465


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": 5432,
    }
}

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]

CELERY_BROKER_URL = "redis://redis:6379/0"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Include the default Django email handler for errors
        # This is what you'd get without configuring logging at all.
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
            # But the emails are plain text by default - HTML is nicer
            "include_html": True,
        },
        # Log to a text file that can be rotated by logrotate
        "logfile": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": "/app/django.log",
        },
    },
    "loggers": {
        # Again, default Django configuration to email unhandled exceptions
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        # Might as well log any errors anywhere else in Django
        "django": {
            "handlers": ["logfile"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
