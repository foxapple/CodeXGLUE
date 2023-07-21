from django.contrib.auth.decorators import user_passes_test, login_required


def user_is_provider(view):
    actual_decorator = user_passes_test(
        lambda u: u.user_profile.is_provider(),
    )
    return login_required(actual_decorator(view))
