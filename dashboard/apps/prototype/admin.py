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


class RateAdmin(FinancePermissions, admin.ModelAdmin):
    pass


admin.site.register(Person, PersonAdmin)
admin.site.register(Rate, RateAdmin)
admin.site.register(Client, ReadOnlyAdmin)
admin.site.register(Project, ReadOnlyAdmin)
admin.site.register(Task, ReadOnlyAdmin)
