import functools
import logging

from common.stdlib import json
from django import http


log = logging.getLogger('jstestnet')


def json_view(f):
    @functools.wraps(f)
    def wrapper(*args, **kw):
        try:
            response = f(*args, **kw)
            status = 200
        except Exception, err:
            # @TODO(kumar) Need to hook into Django's email mailer here
            log.exception("in JSON response")
            response = {
                'success': False,
                'error': True,
                'message': str(err)
            }
            status = 500
        return http.HttpResponse(json.dumps(response),
                                 content_type='application/json',
                                 status=status)
    return wrapper


def post_required(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        if request.method != 'POST':
            return http.HttpResponseNotAllowed(['POST'])
        else:
            return f(request, *args, **kw)
    return wrapper
