# -*- coding: utf-8 -*-


class ReadOnlyPermissions():
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in obj._meta.fields]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class FinancePermissions():
    """
    This Mixin disallows even admin superusers from having permissions
    """

    def is_finance(self, user):
        return user.groups.filter(name='Finance').exists()

    def has_add_permission(self, request, obj=None):
        return self.is_finance(request.user)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return self.is_finance(request.user)
