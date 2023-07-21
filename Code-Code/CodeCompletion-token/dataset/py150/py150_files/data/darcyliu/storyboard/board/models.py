#!/usr/bin/env python
# encoding: utf-8
"""
models.py

Created by Darcy Liu on 2012-03-01.
Copyright (c) 2012 Close To U. All rights reserved.
"""

from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    key = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256,verbose_name='name')
    slug = models.CharField(unique=True,max_length=128,verbose_name='slug')
    sticky = models.BooleanField(default=False)
    meta = models.TextField(blank=True, verbose_name='meta')
    description = models.TextField(blank=True, verbose_name='description')
    ref = models.ForeignKey('self',blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True,verbose_name='created')
    updated = models.DateTimeField(auto_now=True,verbose_name='updated')
    def __unicode__(self):
        result = self.name
        return unicode(result)

class Thread(models.Model):
    key = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256,verbose_name='title')
    text = models.TextField(blank=True, verbose_name='text')
    text_html = models.TextField(blank=True, verbose_name='html')
    Format_Choices = (
            ('0', 'txt'),
            ('1', 'html'),
            ('2', 'markdown'),
            ('3', 'textile'),
        )
    format = models.CharField(verbose_name='format',max_length=1,default=0,choices=Format_Choices)
    release = models.IntegerField(default=0,verbose_name='release')
    author = models.ForeignKey(User,verbose_name='author')
    tag = models.ForeignKey(Tag,verbose_name='tag')
    ref = models.ForeignKey('self',blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True,verbose_name='created')
    updated = models.DateTimeField(auto_now=True,verbose_name='updated')
    def __unicode__(self):
        result = self.title
        return unicode(result)

    # def get_absolute_url(self):
    #   pass

class Favorite(models.Model):
    key = models.AutoField(primary_key=True)
    thread = models.ForeignKey(Thread,verbose_name='thread')
    author = models.ForeignKey(User,verbose_name='author')
    created = models.DateTimeField(auto_now_add=True,verbose_name='created')
    updated = models.DateTimeField(auto_now=True,verbose_name='updated')
    # def __unicode__(self):
    #     result = self.title
    #     return unicode(result)