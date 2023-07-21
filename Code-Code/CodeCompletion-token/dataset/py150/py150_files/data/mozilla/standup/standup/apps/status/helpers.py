import re
from datetime import date, datetime, timedelta

from standup.database.helpers import paginate as _paginate


def paginate(statuses, page=1, startdate=None, enddate=None, per_page=20):
    from standup.apps.status.models import Status
    if startdate:
        statuses = statuses.filter(Status.created >= startdate)
    if enddate:
        statuses = statuses.filter(Status.created <= enddate)
    return _paginate(statuses, int(page), per_page=per_page)


def startdate(request):
    dates = request.args.get('dates')
    day = request.args.get('day')
    week = request.args.get('week')
    if dates == '7d':
        return date.today() - timedelta(days=7)
    elif dates == 'today':
        return date.today()
    elif isday(day):
        return get_day(day)
    elif isday(week):
        return week_start(get_day(week))
    return None


def enddate(request):
    day = request.args.get('day')
    week = request.args.get('week')
    if isday(day):
        return get_day(day) + timedelta(days=1)
    elif isday(week):
        return week_end(get_day(week))
    return None


def isday(day):
    return day and re.match('^\d{4}-\d{2}-\d{2}$', day)


def get_day(day):
    return datetime.strptime(day, '%Y-%m-%d')


def get_weeks(num_weeks=10):
    weeks = []
    current = datetime.now()
    for i in range(num_weeks):
        weeks.append({"start_date": week_start(current), \
            "end_date": week_end(current), \
            "weeks_ago": i })
        current = current - timedelta(7)
    return weeks


def week_start(d):
    """Weeks start on the Monday on or before the given date"""
    d = d - timedelta(d.isoweekday() - 1)
    return datetime(d.year, d.month, d.day, 0, 0, 0)


def week_end(d):
    """Weeks start on the Sunday on or after the given date"""
    d = d + timedelta(7 - d.isoweekday())
    return datetime(d.year, d.month, d.day, 23, 59, 59)
