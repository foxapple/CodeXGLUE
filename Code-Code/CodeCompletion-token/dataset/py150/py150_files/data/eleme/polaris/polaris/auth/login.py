"""
    polaris.auth.login
    ~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    Polaris login manager.
"""

from flask_login import LoginManager

from polaris.models import User

login = LoginManager()
login.login_view = "index.home"


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)
