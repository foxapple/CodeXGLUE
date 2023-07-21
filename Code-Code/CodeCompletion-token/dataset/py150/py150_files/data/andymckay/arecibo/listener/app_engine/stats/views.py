from datetime import datetime, timedelta

from django.contrib.auth.decorators import user_passes_test
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from google.appengine.api.labs import taskqueue

from app.utils import render_plain, safe_int

from stats.utils import count
from stats.models import Stats

registered = {}

def start(request):
    days = safe_int(request.GET.get("days", 1))
    if not days:
        days = 1
    date = (datetime.today() - timedelta(days=days)).date()
    create(date)
    return HttpResponse("total started")

def create(date):
    existing = Stats.all().filter("date = ", date)
    try:
        stats = existing[0]
    except IndexError:
        stats = Stats()
    stats.date = date
    data = dict([(key, None) for key in registered.keys()])
    stats.set_stats(data)
    stats.save()

    for key in registered.keys():
        taskqueue.add(url=reverse("stats-action", kwargs={"action":key, "pk":stats.id}))

def get_action(request, action, pk):
    stats = Stats.get(pk)
    current = stats.get_stats()
    if action not in registered:
        raise ValueError, "Action: %s not registered" % action
    current[action] = registered[action](stats)
    stats.set_stats(current)
    stats.save()
    return render_plain("total done: %s" % current)

def get_total(stats):
    return count(["timestamp_date = ", stats.date],)

def get_status(stats):
    return {
        "500":count(["status = ", "500"], ["timestamp_date = ", stats.date]),
        "404":count(["status = ", "404"], ["timestamp_date = ", stats.date]),
        "403":count(["status = ", "403"], ["timestamp_date = ", stats.date]),
    }

registered["total"] = get_total
registered["status"] = get_status

@user_passes_test(lambda u: u.is_staff)
def view(request):
    stats = Stats.all().filter("completed = ", True).order("date")[:30]
    stats = [ {"object":s, "stats":s.get_stats()} for s in stats ]
    return direct_to_template(request, "stats.html", {
        "stats": stats,
        "nav": {"selected": "stats",}
        })