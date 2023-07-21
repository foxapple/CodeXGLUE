# Model to contain authentication and authorization related assets
from django.http import HttpResponse, HttpResponseBadRequest


def is_admin(user):
    """
    Tests for 'admin' role on a user_id. Returns True/False.
    """
    # Notes to other devs: Do not be tempted to re-write this as a decorator! While a decorator would make
    # adding @RequireAdmin very convenient, we could no longer use it to decide which action to take when
    # the result of an API call would be different for an admin VS a regular user.
    # When written as a True/False returning function, we can use more flexible code such as:
    #   if is_admin() is True:
    #       do_something_drastic()
    #   else:
    #       do_something_less_drastic()
    from api.models import db_model
    dbc = db_model.connect()
    user = dbc.hbuser.find_one({"username": user['username'], "roles": {"$in": ["admin"]}})
    if user is None:
        return False
    else:
        return True


class RequireLogin(object):
    """
    This decorator inspects incoming HTTP request dictionaries for a X-AUTH-TOKEN header.

    If the token is found, it is validated. If the token is invalid or missing, http 401 is returned.
    """

    def __init__(self, role=None):
        self.f = None
        self.required_role = role
        self.token_string = "INVALID"  # valid string that will always fail to validate
        self.username = None
        self.user = None

    def __call__(self, f):
        def wrapped_f(request, *pargs, **kwargs):
            from django.http import HttpResponseForbidden
            self.f = f
            if 'HTTP_X_AUTH_TOKEN' in request.META:
                self.token_string = request.META['HTTP_X_AUTH_TOKEN']
                if self.valid_token():
                    user = self.fetch_user()
                    if user is None:  # The user matching the token has been deleted
                        return HttpResponseBadRequest("Could not obtain user information")
                    if (self.required_role is not None) and (self.required_role not in user['roles']):
                        return HttpResponseForbidden()
                    request.user = user
                    request.token_string = self.token_string
                    return self.f(request, *pargs, **kwargs)

            # 401 Unauthorized if you reach this point
            return HttpResponse(status=401)
        return wrapped_f

    def fetch_user(self):
        """
        Return user matching self.username, otherwise None
        """
        from api.models import db_model
        dbc = db_model.connect()
        return dbc.hbuser.find_one({"username": self.username})

    def valid_token(self):
        """
        Validate token in self.token_string against redis backend.
        """
        from api.models import redis_wrapper
        from django.conf import settings

        r = redis_wrapper.init_redis()
        username = r.get(self.token_string)
        if username is None:
            return False
        else:
            self.username = username
            r.expire(self.token_string, settings.TOKEN_TTL)  # renew the token expiration
            return True