from fredagscafeen.settings.base import *

SECRET_KEY = "This is insecure"
DEBUG = True

SELF_URL = 'http://localhost:8000/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

