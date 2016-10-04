# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, sensitive_post_parameters_m
from django.contrib.admin.utils import unquote
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from dashboard.apps.dashboard.permissions import user_is_finance
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

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=''):
        user = self.get_object(request, unquote(id))
        if user_is_finance(user) and not user_is_finance(request.user):
            raise PermissionDenied
        return UserAdmin.user_change_password(self, request, id, form_url)


admin.site.unregister(User)
admin.site.register(User, DashboardUserAdmin)
