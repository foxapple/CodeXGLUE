#!/usr/bin/env python
import sys

from os.path import dirname, abspath

import django
from django.conf import settings

if not settings.configured:
    test_settings = {
        'DATABASES': {'default': {'ENGINE': 'django.db.backends.sqlite3'}},
        'STATIC_URL': '/static/',
        'INSTALLED_APPS': [
            'django.contrib.admin', 'django.contrib.auth',
            'django.contrib.sessions', 'django.contrib.contenttypes',
            'linkcheck', 'linkcheck.tests.sampleapp',
        ],
        'ROOT_URLCONF': "linkcheck.tests.urls",
        'SITE_DOMAIN': "localhost",
    }
    if django.get_version() >= '1.7':
        test_settings['MIDDLEWARE_CLASSES'] = [
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        ]
    settings.configure(**test_settings)


def runtests(*test_args):
    from django.test.runner import DiscoverRunner

    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    test_runner = DiscoverRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    if django.get_version() >= '1.7':
        django.setup()
    runtests(*sys.argv[1:])
