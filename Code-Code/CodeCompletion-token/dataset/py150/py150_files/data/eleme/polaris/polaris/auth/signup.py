import hashlib
import os

import sqlalchemy as sa

from .form import email_allowed
from ..models import db, User, OauthUser


def local_signup(username, email, password):
    if not email_allowed(email):
        return

    try:
        return db.session.query(User).\
            filter((User.username == username) | (User.email == email)).\
            one()
    except sa.orm.exc.NoResultFound:
        pass

    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user


def oauth_signup(info, provider):
    if not info["email"] or not email_allowed(info["email"]):
        return

    oauth_user = db.session.query(OauthUser).\
        filter(OauthUser.provider_id == str(info["id"])).\
        filter(OauthUser.provider == provider).\
        first()
    if oauth_user:
        return oauth_user.user

    user = db.session.query(User).filter(User.email == info["email"]).first()
    if not user:
        random_pwd = hashlib.sha1(os.urandom(64)).hexdigest()
        user = User(username="{}_{}".format(provider, info["username"]),
                    nickname=info["username"],
                    email=info["email"],
                    password=random_pwd)
        oauth_user = OauthUser(
            user=user,
            provider_info=info,
            provider_id=str(info["id"]),
            provider_email=info["email"],
            provider=provider)
        db.session.add(oauth_user)
        db.session.commit()
        return user
    else:
        oauth_user = OauthUser(
            user=user,
            provider_info=info,
            provider_id=str(info["id"]),
            provider_email=info["email"],
            provider=provider)
        db.session.add(oauth_user)
        db.session.commit()
        return user
