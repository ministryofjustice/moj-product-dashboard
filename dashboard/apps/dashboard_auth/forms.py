# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from dashboard.apps.dashboard.permissions import user_is_finance


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
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but with the appropriate permission, you can change the password "
                    "using <a href=\"../password/\">this form</a>."))


class DashboardUserCreationForm(FinanceAuthFormMixin, UserCreationForm):
    pass
