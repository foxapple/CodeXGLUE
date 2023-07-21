from django.contrib import admin
from .models import Provider, Location, TestDownload, TestIP, Datacenter


class ProviderAdmin(admin.ModelAdmin):
    pass


class TestIPInline(admin.TabularInline):
    model = TestIP


class TestDownloadInline(admin.TabularInline):
    model = TestDownload


class LocationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('city', 'country', 'provider', 'datacenter')
    list_filter = ('created_at', 'updated_at')

    inlines = [
        TestIPInline,
        TestDownloadInline,
    ]

admin.site.register(Provider, ProviderAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Datacenter)