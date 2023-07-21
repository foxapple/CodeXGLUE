from django.contrib import admin
from blog.models import Entry


class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'created_by', 'status')
    list_display_links = ('created_at', 'title')
    list_filter = ('status', 'created_at')
    fields = ('title', 'created_by', 'content', 'status')

    def add_view(self, request):
        self.fields = ('title', 'content', 'status')
        return super(EntryAdmin, self).add_view(request)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

    def publish_entry(self, request, queryset):
        queryset.update(status=Entry.PUBLISHED_STATUS)
    publish_entry.short_description = "Publish selected entries"

    def draft_entry(self, request, queryset):
        queryset.update(status=Entry.DRAFT_STATUS)
    draft_entry.short_description = "Draft selected entries"

    def unpublish_entry(self, request, queryset):
        queryset.update(status=Entry.HIDDEN_STATUS)
    unpublish_entry.short_description = "Unpublish selected entries"

    actions = [publish_entry, draft_entry, unpublish_entry]

admin.site.register(Entry, EntryAdmin)
