#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import re

from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
from microblogging.templatetags.microblogging_tags import (
        render_tweet_text as _render_tweet_text,
        user_ref_re,
        make_user_link,
        smilize
        )

from tagging.templatetags.tagging_tags import tag_ref_re, make_tag_link

register = template.Library()

register.filter("smilize", smilize)

@register.simple_tag
def render_markup_name(post):
    return dict(settings.MARKUP_CHOICES).get(post.markup, '')

@register.simple_tag
def render_tweet_text(tweet):
    """
    Override render_tweet_text from microblogging to make URLs clickable
    """
    text = _render_tweet_text(tweet)
    text = template.defaultfilters.urlize(text)
    return text


@register.inclusion_tag("_user_link.html")
def profile_link(member):
    return {'member': member}


@register.inclusion_tag("_avatar_link.html")
def avatar_link(member, avatar_size):
    return {'member': member, 'avatar_size': avatar_size}

@register.filter
def profilize(text):
    """
    Replace @username by a link to the profile page
    """
    text = user_ref_re.sub(make_user_link, text)
    return mark_safe(text)

@register.filter
def tagalize(text):
    """
    Replace @username by a link to the profile page
    """
    text = tag_ref_re.sub(make_tag_link, text)
    return mark_safe(text)

# uniform filters override to provide bootsrap styles
#

class_converter = {
    "textinput":"textinput textInput",
    #"fileinput":"fileinput fileUpload"
}

@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__.lower() == "checkboxinput"

@register.filter
def is_fileinput(field):
    return field.field.widget.__class__.__name__.lower().endswith("fileinput")

@register.filter
def with_class(field):
    class_name = field.field.widget.__class__.__name__.lower()
    class_name = class_converter.get(class_name, class_name)
    if "class" in field.field.widget.attrs:
        field.field.widget.attrs['class'] += " %s" % class_name
    else:
        field.field.widget.attrs['class'] = class_name

    field.field.widget.attrs['class'] += " form-control"
    return unicode(field)



