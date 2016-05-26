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

    def avatar_tag(self, obj):
        return '<img src="{}" style="height:40px;"/>'.format(obj.avatar)
    avatar_tag.allow_tags = True
    avatar_tag.short_description = 'image'


class RateAdmin(FinancePermissions, admin.ModelAdmin):
    pass


admin.site.register(Person, PersonAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Client, ReadOnlyAdmin)
admin.site.register(Project, ReadOnlyAdmin)
admin.site.register(Task, ReadOnlyAdmin)
