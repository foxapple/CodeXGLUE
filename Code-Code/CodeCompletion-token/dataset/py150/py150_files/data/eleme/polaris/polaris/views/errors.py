"""
    polaris.views.errorhandler
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    Polaris error pages.
"""

import http.client as http

from flask import (
    Blueprint,
    jsonify,
)

errors = Blueprint("errors", __name__)


@errors.errorhandler(http.BAD_REQUEST)
def bad_request(error):
    return jsonify({"error": "Bad request"}), http.BAD_REQUEST


@errors.errorhandler(http.NOT_FOUND)
def not_found(error):
    return jsonify({"error": "Not found."}), http.NOT_FOUND
