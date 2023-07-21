#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import datetime

from django import template
from django.template import Library
from django.template import resolve_variable
from django.core.exceptions import ObjectDoesNotExist
from html2text import html2text as h2t

from intranet.org.models import Scratchpad


register = Library()


@register.filter()
def html2text(value):
    """Convert HTML text to plaintext"""
    return h2t(value)


@register.inclusion_tag('org/box_plache.html')
def box_plache(diarys, user):
    """summarize paid, unpaid time for given period of diaries"""
    list = {}  # Hash<author.username, hours unpaid>
    paylist = {} 	# Hash<author.username, hours paid>
    billable_hours = 0  # total paid time, in hours
    total_hours = 0	 # total paid+unpaid time, in hours
    sum = 0	 # total to be paid (= total paid time * tariff)

    # pupulate list, paylist from diaries
    for o in diarys:
        a = o.author.username
        if a in list:
            list[a] += o.length.hour
        else:
            list[a] = o.length.hour
            paylist[a] = 0
        total_hours += o.length.hour

        # paid projects are dezuranje (22) and tehnicarjenje (23)
        # they must reference an event that requires a technician, also
        if ((o.task.id == 22) or (o.task.id == 23 and o.event != None and (o.event.require_technician or o.event.require_video))):
            paylist[a] += o.length.hour
            billable_hours += o.length.hour

    # compute per-person summaries
    tariff = 3.50   # EUR/hour
    objects = []				# List<Hash<String, Object>> - summaries per person
    for o in list:				# for every author.username
        a = {}					# his summary
        a['name'] = o
        a['time'] = list[o]			# unpaid time in hours
        a['paytime'] = paylist[o]		# paid time in hours
        a['money'] = paylist[o] * tariff  # paid time * tariff (3.13eur/h currently)
        objects.append(a)

        # add to totals
        sum += (paylist[o] * tariff)

    # sort by a['money']
    objects.sort(lambda a, b: int(b['money'] - a['money']))

    return {'objects': objects,
            'user': user,
            'billable_hours': billable_hours,
            'total_hours': total_hours,
            'sum': sum}


@register.inclusion_tag('org/box_scratchpad.html')
def box_scratchpad(user):
    try:
        scratchpad = Scratchpad.objects.latest('id')
    except ObjectDoesNotExist:
        scratchpad = []

    return {'object': scratchpad}


@register.inclusion_tag('org/print_diary.html', takes_context=True)
def print_diary(context, obj):
    context['object'] = obj
    return context


@register.inclusion_tag('org/print_event.html', takes_context=True)
def print_event(context, obj):
    context.update({'event': obj})
    return context


@register.inclusion_tag('org/form_event.html')
def form_event(form):
    return {'form': form}


@register.inclusion_tag('org/box_reccurings.html')
def box_reccurings(form):
    return {'form': form}


def parse(args):
    kwargs = {}
    if args:
        if ',' not in args:
            # ensure at least one ','
            args += ','
        for arg in args.split(','):
            arg = arg.strip()
            if arg == '':
                continue
            kw, val = arg.split('=', 1)
            kw = kw.lower()
            kwargs[kw] = val

    return kwargs


class BoxListNode(template.Node):
    """
    Example usage:
        {% box_list ObjectName "QuerySet" ["template=foo,order_by=bar,limit=:3"] }
        In third parameter, template, order_by and limit are all optional.

        {% box_list Lend "returned=False,from_who__exact=user.id" "template=box/foo.html,order_by=returned,limit=:2" %}

        the templates get extra variable 'today' passed
    """
    def __init__(self, object, queryset, params):
        self.object = object
        self.queryset = queryset
        self.params = params

    def render(self, context):
        kwargs = parse(self.queryset)
        pargs = parse(self.params)

        for i in kwargs:
            if kwargs[i] == 'False':
                kwargs[i] = False
            elif kwargs[i] == 'True':
                kwargs[i] = True
            else:
                kwargs[i] = resolve_variable(kwargs[i], context)
        kwargs = dict([(str(x), kwargs[x]) for x in kwargs.keys()])

        new_queryset = self.object.objects.filter(**kwargs)

        if 'order_by' in pargs:
            new_queryset = new_queryset.order_by(pargs['order_by'])

        if 'limit' in pargs:
            l = pargs['limit']
            i = l.split(':')[0]
            if i:
                i = int(i)
            else:
                i = 0
            j = l.split(':')[1]
            if j:
                j = int(j)
            else:
                j = 0
            new_queryset = new_queryset[i:j]

        if 'template' in pargs:
            template_name = pargs['template']
        else:
            model = new_queryset.model
            template_name = "%s/%s_list.html" % (model._meta.app_label, model._meta.object_name.lower())

        context['object_list'] = new_queryset
        context['today'] = datetime.date.today()
        return template.loader.get_template(template_name).render(context)


@register.tag(name='box_list')
def box_list(parser, token):
    bits = token.split_contents()
    object_name = bits[1]
    queryset = bits[2][1:-1]
    if len(bits) > 3:
        params = bits[3][1:-1]
    else:
        params = ''
    m = __import__("intranet.org.models", '', '', object_name)
    object = getattr(m, object_name)
    return BoxListNode(object, queryset, params)
