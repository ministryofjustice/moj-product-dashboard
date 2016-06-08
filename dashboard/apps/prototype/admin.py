from django.contrib import admin

from .models import (Person, Rate, Client, Project, Task, Cost, Budget, RAG,
                     Note)
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
    exclude = ['raw_data']

    def avatar_tag(self, obj):
        return '<img src="{}" style="height:40px;"/>'.format(obj.avatar)
    avatar_tag.allow_tags = True
    avatar_tag.short_description = 'image'


class RateAdmin(FinancePermissions, admin.ModelAdmin):
    search_fields = ('person__name', 'person__job_title')


class ClientAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'float_id')
    exclude = ['raw_data']


class CostInline(admin.TabularInline):
    model = Cost
    extra = 0


class BudgetInline(admin.TabularInline):
    model = Budget
    extra = 0


class RAGInline(admin.TabularInline):
    model = RAG
    extra = 0


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'float_id', 'is_billable',
              'project_manager', 'client', 'discovery_date', 'alpha_date',
              'beta_date', 'live_date', 'end_date', 'visible']
    exclude = ['raw_data']
    inlines = [CostInline, BudgetInline, RAGInline, NoteInline]
    readonly_fields = ('name', 'description', 'float_id', 'is_billable',
                       'project_manager', 'client')
    search_fields = ('name', 'float_id')


class TaskAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'person__name', 'project__name', 'float_id')
    exclude = ['raw_data']


admin.site.register(Person, PersonAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.register(Project, ProjectAdmin)
admin.site.register(Cost)
admin.site.register(Budget)
admin.site.register(RAG)
admin.site.register(Note)
