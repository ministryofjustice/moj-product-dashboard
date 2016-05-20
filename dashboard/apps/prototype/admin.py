from django.contrib import admin

from .models import Person, Rate, Client, Project, Task


admin.site.register(Person)
admin.site.register(Rate)
admin.site.register(Client)
admin.site.register(Project)
admin.site.register(Task)
