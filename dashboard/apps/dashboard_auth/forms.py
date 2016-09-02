# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from dashboard.apps.prototype.permissions import user_is_finance


class FinanceAuthFormMixin():
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(FinanceAuthFormMixin, self).__init__(*args, **kwargs)

    def clean_groups(self):
        groups = self.cleaned_data.get('groups')
        already_finance = user_is_finance(self.instance) if self.instance else False
        admin_user_is_finance = user_is_finance(self.request.user)
        is_finance_now = settings.FINANCE_GROUP_NAME in [g.name for g in groups]
        if not already_finance and is_finance_now and not admin_user_is_finance:
            raise ValidationError('You must be a Finance user to add finance '
                                  'permissions to a user')
        return groups


class DashboardUserChangeForm(FinanceAuthFormMixin, UserChangeForm):
    pass


class DashboardUserCreationForm(FinanceAuthFormMixin, UserCreationForm):
    pass
