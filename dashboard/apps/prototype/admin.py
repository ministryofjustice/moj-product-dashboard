from django.contrib import admin

from .models import (Person, Rate, Client, Project, Task, Cost, Budget, RAG,
                     Note)
from .permissions import ReadOnlyPermissions, FinancePermissions


class ReadOnlyAdmin(ReadOnlyPermissions, admin.ModelAdmin):
    pass


class RateInline(FinancePermissions, admin.TabularInline):
    model = Rate
    extra = 0


class IsCivilServantFilter(admin.SimpleListFilter):
    """
    this filter shows labels of civil servant or contractor
    instead of boolean flags
    """
    title = 'civil servant | contractor'
    parameter_name = 'is_civil_servant'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Civil Servant'),
            ('no', 'Contractor'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_contractor=False)
        elif self.value() == 'no':
            return queryset.filter(is_contractor=True)


class IsCurrentFilter(admin.SimpleListFilter):
    """
    this filter shows `is_current=True` by default
    """
    title = 'is current staff?'
    parameter_name = 'is_current'

    def lookups(self, request, model_admin):
        return (
            ('all', 'All'),
            (None, 'Yes'),
            ('no', 'No'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(is_current=True)
        elif self.value() == 'no':
            return queryset.filter(is_current=False)


class PersonAdmin(ReadOnlyAdmin):
    inlines = [RateInline]
    ordering = ('name',)
    readonly_fields = ('avatar_tag', )
    list_display = ('avatar_tag', 'name', 'job_title',
                    'contractor_civil_servant', 'is_current')
    search_fields = ('name', 'job_title')
    list_filter = (IsCivilServantFilter, IsCurrentFilter)
    exclude = ['raw_data']

    def avatar_tag(self, obj):  # pragma: no cover
        return '<img src="{}" style="height:40px;"/>'.format(obj.avatar)
    avatar_tag.allow_tags = True
    avatar_tag.short_description = 'image'

    def contractor_civil_servant(self, obj):
        if obj.is_contractor:
            return 'Contractor'
        else:
            return 'Civil Servant'
    contractor_civil_servant.short_description = 'Contractor | Civil Servant'


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
