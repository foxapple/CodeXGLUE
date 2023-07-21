from __future__ import absolute_import, unicode_literals
from django_pg.utils.south import south_installed
import os
import sys


DEBUG = True
TEMPLATE_DEBUG = DEBUG


# Database settings. This assumes that the default user and empty
# password will work.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_pg',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}


# Boilerplate settings.
TIME_ZONE = 'America/Chicago'
USE_TZ = True
LANGUAGE_CODE = 'en-us'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATICFILES_DIRS = ()
SECRET_KEY = 'vu8[/=:+pjz8o:9c6g7spzq_c14ke9zymjq(:m]5_+-gc3l8)]'


# Installed apps. Be smart about this: search for things under the
# `tests/` directory, but add them as applications as they have their
# own models that we need in order to test this stuff.
INSTALLED_APPS = [ 'django_pg', ]
for module in os.listdir(os.path.dirname(__file__)):
    full_dir = os.path.dirname(__file__) + '/' + module
    if os.path.isdir(full_dir) and os.path.isfile(full_dir + '/__init__.py'):
        INSTALLED_APPS.append('tests.' + module)

# If South is installed, then add it to installed apps.
if south_installed:
    INSTALLED_APPS.append('south')

# We don't really care what middleware is installed for our purposes,
# but we really want Django 1.7's check/warning system to be quiet about
# this not being explicitly set.
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

# Easiest default test settings for django-pgfields itself.
DJANGOPG_IMPROVED_REPR = True
DJANGOPG_REPR_TEMPLATE = 'single_line'
