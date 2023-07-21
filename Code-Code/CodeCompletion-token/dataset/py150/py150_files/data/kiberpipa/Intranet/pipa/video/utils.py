import os
import datetime
from zipfile import ZipFile
from cStringIO import StringIO

import requests
from django.template import Template, Context
from django.http import HttpResponse
from django.conf import settings

from intranet.org.models import Event


def _sablona_file(fn):
    return os.path.join(os.path.dirname(__file__), 'sablona', fn)


def prepare_video_zip(slug, title, date, person):
    context = Context({
        'date': title,
        'title': date,
        'predavatelji': person,
    })

    folder_title = slug

    t = Template(open(_sablona_file('default.xml')).read())
    default_xml = t.render(context).encode('utf-8')

    zipfile_file = StringIO()
    zipfile = ZipFile(zipfile_file, "w")
    zipfile.writestr("%s/default.xml" % folder_title, default_xml)

    for fn in ['big_pal_1_2-page3.png', 'big_pal_1_2-page4.png', 'maska_small.png', 'naslovnica_small.png', 'readme']:
        zipfile.write(_sablona_file(fn), '%s/%s' % (folder_title, fn))

    zipfile.close()

    response = HttpResponse(zipfile_file.getvalue(), mimetype="application/zip")
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % folder_title
    return response


def is_streaming():
    """Check if video live stream is running."""
    if getattr(settings, 'LIVE_STREAM_DISABLE', False):
        return False
    try:
        r = requests.head(settings.LIVE_STREAM_URL, timeout=1)
    except (requests.ConnectionError, requests.Timeout):
        return False
    else:
        return 200 <= r.status_code < 300


def get_streaming_event():
    try:
        now = datetime.datetime.now()
        streaming_event = Event.objects.filter(public=True,
                                               start_date__lte=now).order_by('-start_date')[0]
        try:
            next_event = streaming_event.get_next()
        except Event.DoesNotExist:
            streaming_event = next_event
        else:
            td = next_event.start_date - now
            if td.days == 0 and 0 < td.seconds < 1800:
                # if there is 30min to next event, take that one
                streaming_event = next_event
        # TODO: if previous event should have ended more than 3 hours ago, don't display the stream
    except IndexError:
        return

    return streaming_event


def get_next_streaming_event():
    now = datetime.datetime.now()
    q = Event.objects.filter(public=True,
                             require_video=True,
                             start_date__gte=now)
    try:
        return q.order_by('-start_date')[0]
    except IndexError:
        return
