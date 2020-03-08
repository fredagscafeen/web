from fredagscafeen.settings.base import *
import os
import sys

ALLOWED_HOSTS = ['*']
SECRET_KEY = "This is insecure"
DEBUG = True

SELF_URL = 'http://localhost:8000/'

MAILMAN_MUTABLE = False

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

AUTOLOGIN_USERNAME = os.environ.get('AUTOLOGIN_USERNAME')

if sys.argv[1:2] != ["test"]:
    MIDDLEWARE += ('fredagscafeen.autologin.AutologinMiddleware',)
