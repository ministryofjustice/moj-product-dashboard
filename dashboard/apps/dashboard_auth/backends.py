# -*- coding: utf-8 -*-
from django.contrib.auth import backends
from .models import DashboardUser


class ModelBackend(backends.ModelBackend):
    """
    Extending to provide a proxy for user
    """

    def get_user(self, user_id):
        try:
            return DashboardUser.objects.get(pk=user_id)
        except DashboardUser.DoesNotExist:
            return None
