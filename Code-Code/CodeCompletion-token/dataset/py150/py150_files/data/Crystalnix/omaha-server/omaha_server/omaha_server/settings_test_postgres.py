# coding: utf8

import os

os.environ.setdefault('DB_PUBLIC_USER', 'test_public_user')
os.environ.setdefault('DB_PUBLIC_PASSWORD', 'test_public_password')

os.environ.setdefault('OMAHA_SERVER_PRIVATE', 'True')

from .settings import *
DB_PUBLIC_ROLE = os.environ.get('DB_PUBLIC_ROLE', 'test_public_users')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

INSTALLED_APPS += (
    'django_nose',
)

TEST_RUNNER = 'omaha_server.runner.PublicPrivateNoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-coverage',
    '--cover-package=omaha_server,omaha,crash,feedback,sparkle,healthcheck',
    '--cover-inclusive',
    '--nologcapture',
    '-s',
]

# Tricks to speed up Django tests

DEBUG = False
TEMPLATE_DEBUG = False
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_BACKEND = 'memory'

CACHES['default'] = {
    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
}

CACHES['statistics'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': '{REDIS_HOST}:{REDIS_PORT}:{REDIS_DB}'.format(
        REDIS_PORT=os.environ.get('REDIS_STAT_PORT', REDIS_PORT),
        REDIS_HOST=os.environ.get('REDIS_STAT_HOST', REDIS_HOST),
        REDIS_DB=os.environ.get('REDIS_STAT_DB', 13)),
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    }
}


OMAHA_UID_KEY_PREFIX = 'test:uid'

CRASH_SYMBOLS_PATH = os.path.join(BASE_DIR, 'crash', 'tests', 'testdata', 'symbols')
CRASH_S3_MOUNT_PATH = os.path.join(BASE_DIR, 'crash', 'tests', 'testdata')

RAVEN_DSN_STACKTRACE = 'http://c5dc6f5ab74b4ab8a567f545b00cb138:c57ee00766cf497da102b7a83d731840@127.0.0.1/1'
AWS_STORAGE_BUCKET_NAME = 'test'
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

SENTRY_STACKTRACE_DOMAIN = 'test'
SENTRY_STACKTRACE_ORG_SLUG = 'test'
SENTRY_STACKTRACE_PROJ_SLUG ='test'
SENTRY_STACKTRACE_API_KEY = 'test'