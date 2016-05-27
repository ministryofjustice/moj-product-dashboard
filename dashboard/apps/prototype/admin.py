from django.contrib import admin

from .models import Person, Rate, Client, Project, Task
from .permissions import ReadOnlyPermissions, FinancePermissions


class ReadOnlyAdmin(ReadOnlyPermissions, admin.ModelAdmin):
    pass


class RateInline(FinancePermissions, admin.TabularInline):
    model = Rate
    extra = 0


class PersonAdmin(ReadOnlyAdmin):
    inlines = [RateInline]
    readonly_fields = ('avatar_tag', )
    list_display = ('avatar_tag', 'name', 'job_title', 'is_contractor',
                    'is_current')
    search_fields = ('name', 'job_title')

    def avatar_tag(self, obj):
        return '<img src="{}" style="height:40px;"/>'.format(obj.avatar)
    avatar_tag.allow_tags = True
    avatar_tag.short_description = 'image'


class RateAdmin(FinancePermissions, admin.ModelAdmin):
    search_fields = ('person__name', 'person__job_title')


class ClientAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'float_id')


class ProjectAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'float_id')


class TaskAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'person__name', 'project__name', 'float_id')


admin.site.register(Person, PersonAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Task, TaskAdmin)
