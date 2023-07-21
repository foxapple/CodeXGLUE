from django.contrib import admin

from competencies.models import *


# --- Organization admin, with inline subjects ---
class SubjectAreaInline(admin.TabularInline):
    model = SubjectArea
    extra = 1

class OrganizationAdmin(admin.ModelAdmin):
    inlines = [SubjectAreaInline]

# --- Subject Area admin, with subdisciplines inline
class SubdisciplineAreaInline(admin.TabularInline):
    model = SubdisciplineArea
    extra = 1

class SubjectAreaAdmin(admin.ModelAdmin):
    inlines = [SubdisciplineAreaInline]

# --- Subdiscipline Area admin, with competency areas inline
class CompetencyAreaInline(admin.TabularInline):
    model = CompetencyArea
    extra = 1

class SubdisciplineAreaAdmin(admin.ModelAdmin):
    inlines = [CompetencyAreaInline]

# --- Competency Area admin, with performance indicators inline
class EssentialUnderstandingInline(admin.TabularInline):
    model = EssentialUnderstanding
    extra = 1

class CompetencyAreaAdmin(admin.ModelAdmin):
    inlines = [EssentialUnderstandingInline]

# --- Performance Indicator admin, with learning objectives inline
class LearningTargetInline(admin.TabularInline):
    model = LearningTarget
    extra = 1

class EssentialUnderstandingAdmin(admin.ModelAdmin):
    inlines = [LearningTargetInline]

# --- Pathway Admin ---
class PathwayAdmin(admin.ModelAdmin):
    pass


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(SubjectArea, SubjectAreaAdmin)
admin.site.register(SubdisciplineArea, SubdisciplineAreaAdmin)
admin.site.register(CompetencyArea, CompetencyAreaAdmin)
admin.site.register(EssentialUnderstanding, EssentialUnderstandingAdmin)
