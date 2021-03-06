# -*- coding: utf-8 -*-
from django.conf import settings


def user_is_finance(user):
    return user.groups.filter(name=settings.FINANCE_GROUP_NAME).exists()


class ReadOnlyPermissions():
    exclude = []
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in obj._meta.fields
                if field.name not in self.exclude] + self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FinancePermissions():
    """
    This Mixin disallows even admin superusers from having permissions
    """

    def is_finance(self, user):
        return user_is_finance(user)

    def has_add_permission(self, request, obj=None):
        return self.is_finance(request.user)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return self.is_finance(request.user)
