from django.contrib.flatpages.admin import FlatPageAdmin, FlatpageForm
from django.contrib import admin
from django.contrib.flatpages.models import FlatPage
from django.db import models
from django import forms
from flatpage_extend.models import FlatpageNavbar


class FlatpageInline(admin.StackedInline):
    model = FlatpageNavbar
    inline_classes = ('grp-open',)


class BetterFlatPageAdmin(FlatPageAdmin):

    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'class': 'ckeditor'})},
    }

    fieldsets = (
        (None, {
            'fields': ('url', 'title', 'content', 'sites')
        }),
    )

    inlines = [
        FlatpageInline
    ]

    class Media:
        js = ('ckeditor/ckeditor.js',)
        css = {
            'all': ('flat_page_static/css/flatpages_css.css',),
        }


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, BetterFlatPageAdmin)