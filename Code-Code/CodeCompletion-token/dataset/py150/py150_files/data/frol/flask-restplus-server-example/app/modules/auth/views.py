# coding: utf-8
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""

from flask import Blueprint, request, render_template, jsonify
from flask_login import current_user
from werkzeug import security, exceptions as http_exceptions

from app.extensions import db, api, oauth2

from .models import OAuth2Client


auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth') # pylint: disable=invalid-name


@auth_blueprint.route('/oauth2/client')
def client():
    """
    This endpoint creates and provides the authenticated user with
    ``client_id`` and ``client_secret``.
    """
    if not current_user.is_authenticated:
        return api.abort(code=http_exceptions.Unauthorized.code)
    # XXX: remove hard-codings
    # TODO: reconsider using gen_salt
    # TODO: develop sensible scopes
    # TODO: consider moving `db` operations into OAuth2Client class implementation
    client_instance = OAuth2Client(
        client_id=security.gen_salt(40),
        client_secret=security.gen_salt(50),
        _redirect_uris=' '.join([
            'http://localhost:8000/authorized',
            'http://127.0.0.1:8000/authorized',
            'http://127.0.0.1:5000/api/v1/o2c.html',
            'http://127.0.0.2:8000/authorized',
            'http://127.0.1:8000/authorized',
            'http://127.1:8000/authorized',
            ]),
        _default_scopes='users:read users:write email',
        user_id=current_user.id,
    )
    db.session.add(client_instance)
    db.session.commit()
    return jsonify(
        client_id=client_instance.client_id,
        client_secret=client_instance.client_secret,
    )

@auth_blueprint.route('/oauth2/token', methods=['GET', 'POST'])
@oauth2.token_handler
def access_token(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint is for exchanging/refreshing an access token.

    Returns a dictionary or None as the extra credentials for creating the
    token response.

    :param *args: Variable length argument list.
    :param **kwargs: Arbitrary keyword arguments.
    """
    return None

@auth_blueprint.route('/oauth2/revoke', methods=['POST'])
@oauth2.revoke_handler
def revoke_token():
    """
    This endpoint allows a user to revoke their access token.
    """
    pass

@auth_blueprint.route('/oauth2/authorize', methods=['GET', 'POST'])
@oauth2.authorize_handler
def authorize(*args, **kwargs):
    # pylint: disable=unused-argument
    """
    This endpoint asks user if he grants access to his data to the requesting
    application.
    """
    # TODO: improve implementation
    if not current_user.is_authenticated:
        return api.abort(code=http_exceptions.Unauthorized.code)
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        oauth2_client = OAuth2Client.query.filter_by(client_id=client_id).first()
        kwargs['client'] = oauth2_client
        kwargs['user'] = current_user
        # TODO: improve template design
        return render_template('authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'
