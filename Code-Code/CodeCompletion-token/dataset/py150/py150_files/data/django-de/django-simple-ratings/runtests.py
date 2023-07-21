#!/usr/bin/env python
import sys
import django

from os.path import dirname, abspath

from django.conf import settings

if len(sys.argv) > 1 and 'postgres' in sys.argv:
    sys.argv.remove('postgres')
    db_engine = 'django.db.backends.postgresql_psycopg2'
    db_name = 'test_main'
else:
    db_engine = 'django.db.backends.sqlite3'
    db_name = ''

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': db_engine,
                'NAME': db_name,
            }
        },
        DATABASE_ENGINE = db_engine,
        DATABASE_NAME = db_name,
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'ratings',
            'ratings.ratings_tests',
        ],
        MIDDLEWARE_CLASSES = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
        ),
        ROOT_URLCONF='ratings.ratings_tests.urls',
    )

if django.VERSION < (1, 6):
    app_to_test = 'ratings_tests'
else:
    app_to_test = 'ratings.ratings_tests'

try:
    from django.test.simple import run_tests
    def runtests(*test_args):
        if not test_args:
            test_args = [app_to_test]
        parent = dirname(abspath(__file__))
        sys.path.insert(0, parent)
        failures = run_tests(test_args, verbosity=1, interactive=True)
        sys.exit(failures)

    if __name__ == '__main__':
        runtests(*sys.argv[1:])

except:
    from django.test.utils import get_runner
    def runtests(*test_args):
        if not test_args:
            test_args = [app_to_test]
        parent = dirname(abspath(__file__))
        sys.path.insert(0, parent)
        TestRunner = get_runner(settings)
        test_runner = TestRunner(verbosity=1, interactive=True)
        try:
            from django import setup
            setup()
        except ImportError:
            pass
        failures = test_runner.run_tests(test_args)
        sys.exit(failures)

    if __name__ == '__main__':
        runtests(*sys.argv[1:])
