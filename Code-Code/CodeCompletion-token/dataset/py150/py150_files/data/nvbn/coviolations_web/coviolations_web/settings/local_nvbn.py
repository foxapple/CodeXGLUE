DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': '',
    }
}

VIOLATIONS = (
    'violations.dummy',
    'violations.pep8',
    'violations.sloccount',
    'violations.py_unittest',
    'violations.pip_review',
    'violations.testem',
    'violations.coverage',
    'violations.jslint',
    'violations.xunit',
)

SERVICES = (
    'services.dummy',
    'services.travis_ci',
    'services.token',
)

MONGO_CLIENT_ARGUMENTS = []
MONGO_DB = 'coviolations'

REDIS_PUSH = 'covio_push'
PUSH_BIND = 'http://localhost:9999/sub'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'nodes': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
}
