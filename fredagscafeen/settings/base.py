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

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

CONSTANCE_CONFIG = {
    "REGISTRATION_OPEN": (True, "Er bartendertilmelding åben?", bool),
    "SEND_REMINDERS": (
        True,
        "Skal der sendes ugentlige barvagt og pantvagt reminders?",
        bool,
    ),
    "BANNER_HTML": ("", "HTML banner", str),
}

SECRET_ADMIN_KEYS = [
    (
        "MAILMAN",
        "Alle, Best og Fest mailinglist admin password",
        "best@fredagscafeen.dk",
        "https://maillist.au.dk/postorius/lists/",
    ),
    (
        "GOOGLE_PASSWORD",
        "Google password",
        "datcafe@gmail.com",
        "https://gmail.com/",
    ),
    (
        "INSTAGRAM_PASSWORD",
        "Instagram password",
        "fredagscafeen.dk",
        "https://www.instagram.com/",
    ),
    (
        "CONTABO_PASSWORD",
        "Contabo password",
        "best@fredagscafeen.dk",
        "https://my.contabo.com/account/login",
    ),
    (
        "MIDTTRAFIK_BESTILLING_PASSWORD",
        "midttrafikbestilling.dk password",
        "fredagscafeen",
        "https://midttrafikbestilling.dk/",
    ),
    (
        "CLOUDFLARE_PASSWORD",
        "Cloudflare password",
        "best@fredagscafeen.dk",
        "https://dash.cloudflare.com/",
    ),
    (
        "ZETTLE_PASSWORD",
        "Zettle password",
        "best@fredagscafeen.dk",
        "https://my.zettle.com/",
    ),
    (
        "BEVCO_PASSWORD",
        "Bevco password",
        "best@fredagscafeen.dk",
        "https://www.bevco.dk/login",
    ),
    (
        "DRINX_PASSWORD",
        "Drinx password, Kunde nr. 27973647",
        "fredag",
        "https://drinx.dk/login",
    ),
    (
        "KARET_PASSWORD",
        "Hængelås-kodeord til karet",
        None,
        None,
    ),
    (
        "KOELESKABE_PASSWORD",
        "Hængelås-kodeord til køleskabene i Nygaardkælderen",
        None,
        None,
    ),
    (
        "BIZAY_PASSWORD",
        "Bizay password",
        "best@fredagscafeen.dk",
        "https://www.bizay.dk/Account/Login",
    ),
    (
        "DISCORD_PASSWORD",
        "Discord password",
        "datcafe@gmail.com",
        "https://discord.com/channels/@me",
    ),
]


load_dotenv()

# Inject all secret keys
for k, *_ in SECRET_ADMIN_KEYS:
    v = os.getenv(k)
    if v != None:
        globals()[k] = v
    else:
        print("WARNING: Missing secret key in env:", k)


BOOTSTRAP3 = {
    "success_css_class": "",
}


# SECURITY WARNING: don't run with debug turned on in production!

# ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_object_actions",
    "django_extensions",
    "constance",
    "constance.backends.database",
    "rest_framework.authtoken",
    "bootstrap3",
    "bootstrap_datepicker_plus",
    "captcha",
    "rest_framework",
    "django_celery_beat",
    "corsheaders",
    "items",
    "bartenders",
    "web",
    "api",
    "reminder",
    "udlejning",
    "logentry_admin",
    "bartab",
    "email_auth",
    "guides",
    "events",
    "printer",
    "rosetta",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Used for internationalization. Has to be after sessions but before common
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "email_auth.auth.EmailTokenBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ),
}

ROOT_URLCONF = "fredagscafeen.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["web/templates", "fredagscafeen/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "constance.context_processors.config",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "fredagscafeen.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "da"

TIME_ZONE = "Europe/Copenhagen"

USE_I18N = True

USE_L10N = True

USE_TZ = True

DJANGO_CELERY_BEAT_TZ_AWARE = False

from django.utils.translation import gettext_lazy as _

LANGUAGES = (
    ("da", _("Danish")),
    ("en", _("English")),
)

PARLER_LANGUAGES = {
    None: (
        {
            "code": "da",
        },
        {
            "code": "en",
        },
    ),
    "default": {
        "fallbacks": ["da"],
        "hide_untranslated": False,
    },
}

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale/"),)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

LOGIN_URL = "/login/"

# Use the new NoCaptcha
NOCAPTCHA = True

# CORS Setup
CORS_URLS_REGEX = r"^/api/.*$"  # Only allow CORS requests in /api
CORS_ORIGIN_ALLOW_ALL = True

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

# Server admins (get an email when server errors happen)
ADMINS = [
    ("Jonathan Eilath", "201804772@post.au.dk"),
    ("Anders Bruun Severinsen", "202204885@post.au.dk"),
]

# Allow more fields in GET/POST requests (necessary for BarTabAdmin to function with large snapshots)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10**6

# Session cookie lasts a year
SESSION_COOKIE_AGE = 365 * 24 * 60 * 60

X_FRAME_OPTIONS = "SAMEORIGIN"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
