# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .forms import DashboardUserChangeForm, DashboardUserCreationForm


class DashboardUserAdmin(UserAdmin):
    form = DashboardUserChangeForm
    add_form = DashboardUserCreationForm

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(DashboardUserAdmin, self).get_form(request, obj,
                                                             **kwargs)

        class ModelFormMetaClass(ModelForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return ModelForm(*args, **kwargs)

        return ModelFormMetaClass


admin.site.unregister(User)
admin.site.register(User, DashboardUserAdmin)
