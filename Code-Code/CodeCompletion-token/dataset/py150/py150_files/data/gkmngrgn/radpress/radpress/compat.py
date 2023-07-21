from django import VERSION as DJANGO_VERSION
from django.conf import settings


def get_user_model():
    """
    Returns the user model to use at runtime.
    :return: User or custom user
    """
    if DJANGO_VERSION >= (1, 5):
        from django.contrib.auth import get_user_model

        return get_user_model()  # NOQA
    else:
        from django.contrib.auth.models import User  # NOQA
        return User


def import_user_model():
    """
    Returns the user model to use at import time.
    :return: User, custom user or string
    """
    if DJANGO_VERSION >= (1, 7):
        return settings.AUTH_USER_MODEL
    else:
        return get_user_model()


def has_app(app_name):
    """
    Determines whether an app is listed in INSTALLED_APPS or the app registry.
    :param app_name: string
    :return: bool
    """
    if DJANGO_VERSION >= (1, 7):
        from django.apps import apps
        return apps.is_installed(app_name)
    else:
        from django.conf import settings

        return app_name in settings.INSTALLED_APPS