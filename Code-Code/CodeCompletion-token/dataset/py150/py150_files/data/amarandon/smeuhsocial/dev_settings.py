# To activate these settings as the current local_settings, create a symlink
# called local_settings.py pointing to this file.

from secret_settings import STAGING_DB_PASSWORD, SECRET_KEY

import os

DEBUG = True
SITE_ID = 1

PROJECT_ROOT = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media")
MEDIA_URL = '/site_media/'
STATIC_ROOT = os.path.join(MEDIA_ROOT, "static")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": os.path.join(PROJECT_ROOT, "db", "dev.db"),                       # Or path to database file if using sqlite3.
        "USER": "",                             # Not used with sqlite3.
        "PASSWORD": "",                         # Not used with sqlite3.
        "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    },
#    "defaultXXX": {
#    "ENGINE": "django.db.backends.postgresql_psycopg2",
#    "NAME": "smeuhsocial_staging",
#    "USER": "smeuhsocial_staging",
#    "PASSWORD": STAGING_DB_PASSWORD,
#        "HOST": "localhost",                             # Set to empty string for localhost. Not used with sqlite3.
#        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
#    }
}

DEFAULT_HTTP_PROTOCOL = "https"
DEFAULT_FROM_EMAIL = 'al@smeuh.org'
