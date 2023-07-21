import os
import urlparse
from .base import *

# Heroku needs Gunicorn specifically.
INSTALLED_APPS += ['gunicorn']

SECRET_KEY = os.environ['SECRET_KEY']

#
# Now lock this sucker down.
#
INSTALLED_APPS += ['djangosecure']
MIDDLEWARE_CLASSES.insert(0, 'djangosecure.middleware.SecurityMiddleware')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# The header Heroku uses to indicate SSL:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Canoncalize on "dashboard.djangoproject.com"
MIDDLEWARE_CLASSES.insert(0, 'dashboard.middleware.CanonicalDomainMiddleware')
CANONICAL_HOSTNAME = 'dashboard.djangoproject.com'

#
# Store files on S3, pulling config from os.environ.
#
DEFAULT_FILE_STORAGE = STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_S3_SECURE_URLS = True
AWS_QUERYSTRING_AUTH = False

#
# Pull the various config info from Heroku.
# Heroku adds some of this automatically if we're using a simple settings.py,
# but we're not and it's just as well -- I like doing this by hand.
#

# Make sure urlparse understands custom config schemes.
urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('redis')

# Grab database info
db_url = urlparse.urlparse(os.environ['DATABASE_URL'])
DATABASES = {
    'default': {
        'ENGINE':  'django.db.backends.postgresql_psycopg2',
        'NAME':     db_url.path[1:],
        'USER':     db_url.username,
        'PASSWORD': db_url.password,
        'HOST':     db_url.hostname,
        'PORT':     db_url.port,
    }
}

# Now do redis and the cache.
redis_url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '{0}:{1}'.format(redis_url.hostname, redis_url.port),
        'OPTIONS': {
            'DB': 0,
            'PASSWORD': redis_url.password,
        },
        'VERSION': os.environ.get('CACHE_VERSION', 0),
    },
}

# Use Sentry for debugging if available.
if 'SENTRY_DSN' in os.environ:
    INSTALLED_APPS += ["raven.contrib.django"]
