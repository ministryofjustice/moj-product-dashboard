# -*- coding: utf-8 -*-
from django.contrib.auth.models import User


class DashboardUser(User):
    class Meta:
        proxy = True
        app_label = 'dashboard_auth'

    @property
    def is_finance(self):
        return self.groups.filter(name='Finance').exists()
