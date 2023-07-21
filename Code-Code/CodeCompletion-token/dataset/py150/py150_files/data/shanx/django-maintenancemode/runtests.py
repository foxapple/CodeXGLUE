#!/usr/bin/env python

import re
import sys
from os import path

import django
from django.conf import settings, global_settings
from django.core.management import execute_from_command_line


if not settings.configured:
    BASE_DIR = path.dirname(path.realpath(__file__))

    settings.configure(
        DEBUG = False,
        TEMPLATE_DEBUG = True,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.contenttypes',
            'django.contrib.sites',

            'maintenancemode',
        ),
        MIDDLEWARE_CLASSES = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',

            'maintenancemode.middleware.MaintenanceModeMiddleware',
        ),
        TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner' if django.VERSION < (1,6) else 'django.test.runner.DiscoverRunner',
        SITE_ID = 1,
        ROOT_URLCONF = 'maintenancemode.tests',
        MAINTENANCE_MODE = True,  # or ``False`` and use ``maintenance`` command
        MAINTENANCE_IGNORE_URLS = (
            re.compile(r'^/ignored.*'),
        ),
    )

def runtests():
    argv = sys.argv[:1] + ['test', 'maintenancemode'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runtests()
