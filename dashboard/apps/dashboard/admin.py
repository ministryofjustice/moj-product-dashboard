from datetime import date
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import permission_required
from django.core import urlresolvers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.html import format_html

from dashboard.apps.dashboard.spreadsheets import Export
from .models import (Person, Rate, Area, Product, Cost, Budget,
                     ProductStatus, ProductGroupStatus, Saving, Link,
                     PersonCost, Department, Skill)
from .permissions import ReadOnlyPermissions, FinancePermissions
from .filters import (
    IsVisibleFilter, IsCivilServantFilter, IsCurrentStaffFilter, HasRateFilter)


class ReadOnlyAdmin(ReadOnlyPermissions, admin.ModelAdmin):
    pass


class RateInline(FinancePermissions, admin.TabularInline):
    model = Rate
    extra = 0


class PersonCostInline(FinancePermissions, admin.TabularInline):
    model = PersonCost
    extra = 0


class PersonAdmin(ReadOnlyAdmin, FinancePermissions):
    inlines = [RateInline, PersonCostInline]
    ordering = ('name',)
    list_display = ('name', 'department', 'job_title', 'get_skills',
                    'contractor_civil_servant', 'is_current')
    search_fields = ('name', 'job_title', 'department__name', 'skills__name')
    list_filter = (IsCivilServantFilter, IsCurrentStaffFilter, HasRateFilter)
    fields = ['name', 'staff_number', 'job_title', 'email',
              'is_contractor', 'is_current', 'get_skills', 'float_link']
    readonly_fields = ['float_link', 'get_skills']
    actions = None

    def get_readonly_fields(self, request, obj=None):
        fields = super(PersonAdmin, self).get_readonly_fields(request, obj)
        if not obj.staff_number:
            fields.remove('staff_number')
        return fields

    def contractor_civil_servant(self, obj):
        return obj.type
    contractor_civil_servant.short_description = 'Contractor | Civil Servant'

    def float_link(self, obj):
        return format_html('<a href="{base}/people?active=1&people={name}"'
                           ' target="_blank" rel="external">{float_id}</a>',
                           base=settings.FLOAT_URL,
                           name=obj.name,
                           float_id=obj.float_id)
    float_link.short_description = 'Float Id'
    float_link.allow_tags = True

    def get_skills(self, obj):
        html = [
            '<a href="{}">{}</a>'.format(skill.admin_url, skill.name)
            for skill in obj.skills.all()
        ]
        return ', '.join(html)
    get_skills.short_description = 'Skills'
    get_skills.allow_tags = True

    def get_urls(self):
        urls = [
            url(
                r'^export_rates/$',
                self.admin_site.admin_view(self.export_person_rates_view),
                name='person_export_rates'),
        ]
        return urls + super(PersonAdmin, self).get_urls()

    @method_decorator(permission_required('dashboard.export_person_rates',
                                          raise_exception=True))
    def export_person_rates_view(self, request, *args, **kwargs):
        if not self.is_finance(request.user):
            raise PermissionDenied
        today = date.today()
        export = Export({'date': today, 'title': 'Rate Export'})

        fname = '%s_%s.xlsx' % (
            'RateData',
            today.strftime('%Y-%m-%d'))
        workbook = export.export()
        response = HttpResponse(
            content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'attachment; filename=%s' \
                                          % fname
        workbook.save(response)
        return response


class RateAdmin(FinancePermissions, admin.ModelAdmin):
    search_fields = ('person__name', 'person__job_title')


class AreaAdmin(admin.ModelAdmin):
    search_fields = ('name', 'float_id')
    fields = ['id', 'name', 'float_id', 'manager', 'visible', 'get_products']
    readonly_fields = ['id', 'name', 'float_id', 'get_products']
    exclude = ['raw_data']
    actions = None

    def view_on_site(self, obj):
        return urlresolvers.reverse('service_html', args=[str(obj.id)])

    def get_products(self, obj):
        html = [
            '<a href="{}">{}</a>'.format(product.admin_url, product.name)
            for product in obj.products.all()
        ]
        return format_html(', '.join(html))
    get_products.short_description = 'Products'
    get_products.allow_tags = True


class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name', 'person__name')
    fields = ['id', 'name', 'get_people']
    readonly_fields = ['id', 'name', 'get_people']
    list_display = ('name', 'get_people')
    actions = None

    def get_people(self, obj):
        html = [
            '<a href="{}">{}</a>'.format(person.admin_url, person.name)
            for person in obj.persons.all()
        ]
        return format_html(', '.join(html))
    get_people.short_description = 'People'
    get_people.allow_tags = True


class CostInline(admin.TabularInline):
    model = Cost
    extra = 0


class BudgetInline(admin.TabularInline):
    model = Budget
    extra = 0


class ProductStatusInline(admin.TabularInline):
    model = ProductStatus
    extra = 0


class ProductGroupStatusInline(admin.TabularInline):
    model = ProductGroupStatus
    extra = 0


class SavingInline(admin.TabularInline):
    model = Saving
    extra = 0


class LinkInline(admin.TabularInline):
    model = Link
    extra = 0


class ProductAdmin(admin.ModelAdmin, FinancePermissions):
    fields = ['name', 'description', 'float_link', 'area',
              'product_manager', 'delivery_manager',
              'discovery_date', 'alpha_date', 'beta_date', 'live_date',
              'end_date', 'visible']
    exclude = ['raw_data']
    inlines = [CostInline, BudgetInline, SavingInline, ProductStatusInline,
               LinkInline]
    readonly_fields = ('name', 'description', 'float_link', 'area')
    list_display = ('name', 'status', 'phase', 'area')
    search_fields = ('name', 'float_id')
    list_filter = (IsVisibleFilter, 'area')
    actions = None

    def view_on_site(self, obj):
        return urlresolvers.reverse('product_html', args=[str(obj.id)])

    def float_link(self, obj):
        return format_html('<a href="{base}/projects?active=1&project={name}"'
                           ' target="_blank" rel="external">{float_id}</a>',
                           base=settings.FLOAT_URL,
                           name=obj.name,
                           float_id=obj.float_id)
    float_link.short_description = 'Float Id'
    float_link.allow_tags = True


class TaskAdmin(ReadOnlyAdmin):
    search_fields = ('name', 'person__name', 'product__name', 'float_id')
    exclude = ['raw_data']


class ProductGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('products', )
    list_display = ('name', 'render_products')
    inlines = [ProductGroupStatusInline]

    def render_products(self, obj):  # pragma: no cover
        return '<br/>'.join([
            '<a href="{}"/>{}</a>'.format(p.admin_url, p.name)
            for p in obj.products.all()])
    render_products.short_description = 'Products'
    render_products.allow_tags = True
    actions = None


class DepartmentAdmin(ReadOnlyAdmin):
    search_fields = ['name', 'float_id', 'persons__name']
    actions = None
    list_display = ['name', 'get_people']
    fields = ['name', 'get_people']
    readonly_fields = ['name', 'get_people']
    exclude = ['raw_data']

    def get_people(self, obj):
        html = [
            '<a href="{}">{}</a>'.format(person.admin_url, person.name)
            for person in obj.persons.filter(is_current=True)
        ]
        return format_html(', '.join(html))
    get_people.short_description = 'People'
    get_people.allow_tags = True


admin.site.register(Area, AreaAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(LogEntry, ReadOnlyAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Skill, SkillAdmin)
