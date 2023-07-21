
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.views.decorators.http import require_POST

from helpers import *


@require_POST
@login_required
def subscribe(request, topic_slug):
    topic = get_topic(request, topic_slug)
    subs = SubscribedUser.objects.subscribe_user(user=request.user, topic=topic, group='Member')
    if request.REQUEST.has_key('ajax'):
        dom = '<a href="%s" class="unsubscribe">unsubscribe</a>' % topic.unsubscribe_url()
        payload = dict(action='subscribe', topic=topic.name, id=topic.id, dom=dom)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(topic.get_absolute_url())


@require_POST
@login_required
def unsubscribe(request, topic_slug):
    #import ipdb; ipdb.set_trace()
    topic = get_topic(request, topic_slug)
    try:
        subs = SubscribedUser.objects.get(user=request.user, topic=topic)
        subs.delete()
    except SubscribedUser.DoesNotExist:
        pass
    except CanNotUnsubscribe:
        payload = "<em>Ouch. You created this topic. You can not unsubscribe from this.</em>"
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    if request.REQUEST.has_key('ajax'):
        dom = '<a href="%s" class="subscribe">subscribe</a>' % topic.subscribe_url()
        payload = dict(action='subscribe', topic=topic.name, id=topic.id, dom=dom)
        return HttpResponse(simplejson.dumps(payload), mimetype='text/json')
    return HttpResponseRedirect(topic.get_absolute_url())
