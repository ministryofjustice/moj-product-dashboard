from django.contrib import admin

from . models import *
# Register your models here.

admin.site.register(Person)
admin.site.register(Project)
admin.site.register(Role)
admin.site.register(Rate)
admin.site.register(PersonRole)
admin.site.register(Client)
admin.site.register(Task)
