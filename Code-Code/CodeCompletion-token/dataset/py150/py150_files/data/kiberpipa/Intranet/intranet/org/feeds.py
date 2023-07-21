import datetime

from django.contrib.syndication.views import Feed
from django.contrib.auth.models import User

from intranet.org.models import Diary, Event


today = datetime.date.today()
yesterday = today - datetime.timedelta(days=3)
nextday = today + datetime.timedelta(days=8)


class LatestDiarys(Feed):
    title = "Intranet: Latest diarys"
    link = "/intranet/diarys/"
    description = "Zadnjih 10 kiberpipinih dnevnikov"

    def items(self):
        return Diary.objects.order_by('-pub_date')[:10]


class LatestEvents(Feed):
    title = "Intranet: Latest Events"
    link = "/intranet/events/"
    description = "Aktualni kiberpipini dogodki"

    def items(self):
        return Event.objects.filter(start_date__range=(today, nextday)).order_by('-start_date')[:15]


class ToDo(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise User.ObjectDoesNotExist
        return User.objects.filter(username__exact=bits[0]).get()

    def title(self, obj):
        return "Intranet: odgovornosti za %s" % obj.username

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return "Odgovonosti, ki so dolocene uporabniku %s" % obj.username

    def items(self, obj):
        return []
