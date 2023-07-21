"""
    Generic view helpers live here.
"""
import pytz
import json

from dateutil.parser import parse

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.validators import URLValidator
from django.shortcuts import HttpResponse
from django.utils import timezone

from common.npl.date_parser import DateRangeParser
from notifications.models import Notification


def JSONResponse(payload):
    """
    Helper to return HttpResponse with json type
    json.dumps the payload given
    """
    return HttpResponse(json.dumps(payload), mimetype='application/json')


def NotImplementedResponse():
    return JSONResponse({'error': "NotYetImplemented"})


def _template_values(request, page_title='',
                     navbar='', sub_navbar='', not_count=None, **kwargs):
    
    if not not_count:
        if request.user.is_authenticated():
            not_count = Notification.objects.filter(recipient=request.user, seen=False).count()
        else:
            not_count = 0
        
    template_values = {
        'page_title': page_title,
        navbar: 'active',
        sub_navbar: 'active',
        'user': request.user,
        "notification_count": not_count,
    }

    return dict(template_values.items() + kwargs.items())


def _get_query(request):
    """
        Get query parameters if search is used
    """
    query = request.GET.get("query", "")
    date = request.GET.get("date", "")
    timestamp = request.GET.get("timestamp", None)
    sort = request.GET.get("sort", "top").lower()
    filter = request.GET.get("filter", "following").lower()

    if timestamp:
        t = parse(timestamp, ignoretz=True)
        timestamp = pytz.utc.localize(t)
    else:
        timestamp = timezone.now()

    start_time = ''
    end_time = ''

    if date:
        start_time, end_time = DateRangeParser().parse(date)

    get_dict = {
        "query": query,
        "filter": filter,
        "sort": sort,
        "start_time": start_time,
        "end_time": end_time,
        "username": request.GET.get("username", ""),
        "orderBy": request.GET.get("orderBy", "start_time"),
        "direction": request.GET.get("direction", ""),
        "template": request.GET.get("template", ""),
        "type": request.GET.get("type", ""),
        "page": request.GET.get("page", 1),
        'timestamp': timestamp,
    }

    return get_dict, query, date, sort, filter


def validateEmail(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def validate_url(url):
    if not url.count('://'):
        url = "http://" + url
    validate = URLValidator(verify_exists=True)
    try:
        validate(url)
        return True
    except ValidationError:
        return False
