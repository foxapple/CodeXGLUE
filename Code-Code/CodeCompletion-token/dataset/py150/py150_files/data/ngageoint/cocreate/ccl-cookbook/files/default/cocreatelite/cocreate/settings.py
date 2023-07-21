"""
Django settings for CoCreate:Lite project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
DIRNAME = os.path.dirname(__file__)

VERSION = "1.0.0"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pvf(48&0i@ca2s&@goo&t=&8e30ens#&po+7l$4l!q2=s2i1iy'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []
# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap3',
    'cocreate',
    'debug_toolbar',
    'omnibus',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)
#'registration',
#'registration.supplements.default',

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

RAISE_EXCEPTIONS = True

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
)

ROOT_URLCONF = 'cocreate.urls'

WSGI_APPLICATION = 'cocreate.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Eastern'

USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
STATIC_ROOT = '/opt/cocreate/static/'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, "static_source"),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'omnibus.context_processors.omnibus',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, "templates"),

    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

BOOTSTRAP3 = {
    'jquery_url': "/static/js/jquery-2.1.1.min.js",
    'javascript_url': '/static/js/bootstrap.min.js',
    'css_url': '/static/css/bootstrap.min.css',
    'javascript_in_head': True
    
}

# Email control

# Use these to send email to server
#EMAIL_HOST = "smtp.example.com"
#EMAIL_PORT = "25"

# Use this to send email to console rather than to server
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ADMINS = ( ("Admin", "admin@example.com"), )

# Registration settings
ACCOUNT_ACTIVATION_DAYS = 7

try:
    from .local_settings import *
except ImportError:
    pass

# for django_omnibus
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

TEMPLATE_CONTEXT_PROCESSORS += (
    'omnibus.context_processors.omnibus',
)    

OMNIBUS_ENDPOINT_SCHEME = 'http'  # 'ws' is used for websocket connections
OMNIBUS_WEBAPP_FACTORY = 'omnibus.factories.sockjs_webapp_factory'
OMNIBUS_CONNECTION_FACTORY = 'omnibus.factories.sockjs_connection_factory'
