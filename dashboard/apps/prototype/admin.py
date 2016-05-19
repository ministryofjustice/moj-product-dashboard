from django.contrib import admin

from .models import Person, Role, Rate, PersonRole, Client, Project, Task


admin.site.register(Person)
admin.site.register(Role)
admin.site.register(Rate)
admin.site.register(PersonRole)
admin.site.register(Client)
admin.site.register(Project)
admin.site.register(Task)
