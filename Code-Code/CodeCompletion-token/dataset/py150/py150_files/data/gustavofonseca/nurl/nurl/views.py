from .domain import Url
from .domain import ShortenGenerationError, NotExists

from pyramid.view import view_config
from pyramid.response import Response
from pyramid import httpexceptions


@view_config(route_name='home', renderer='templates/home.pt')
def home(request):

    response_dict = {'project':'nurl'}

    incoming_url = request.params.get('url')
    if incoming_url is not None:
        try:
            short_url = url_shortener(request)
        except httpexceptions.HTTPBadRequest:
            errors = response_dict.setdefault('errors', [])
            response_dict['errors'].append(('Invalid URL',
                "Maybe this hostname is not allowed or you've typed something wrong."))
        else:
            response_dict.update({'short_url': short_url})

    return response_dict

@view_config(route_name='shortener_v1', renderer='jsonp')
def url_shortener(request):

    incoming_url = request.params.get('url')
    if not incoming_url:
        raise httpexceptions.HTTPBadRequest()

    try:
        url_handler = Url(request, url=incoming_url)
    except ValueError:
        raise httpexceptions.HTTPBadRequest()

    try:
        short_url = url_handler.shorten()
    except ShortenGenerationError:
        raise httpexceptions.HTTPInternalServerError()

    return short_url

@view_config(route_name='shortened')
def short_ref_resolver(request):

    url_handler = Url(request, short_url=request.matchdict['short_ref'])
    try:
        plain_url = url_handler.resolve()
    except NotExists:
        raise httpexceptions.HTTPNotFound()

    raise httpexceptions.HTTPMovedPermanently(plain_url)