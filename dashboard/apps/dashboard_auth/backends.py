# -*- coding: utf-8 -*-
from django.contrib.auth import backends
from django.core.validators import validate_email, ValidationError
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

    def authenticate(self, username=None, password=None):
        """
        this method supports authentication using both username and email
        :param username: username or email
        :param password: password
        :return: user object if authenticated or None if not
        """
        try:
            validate_email(username)
        except ValidationError:
            pass
        else:
            try:
                username = DashboardUser.objects.get(email=username).username
            except DashboardUser.DoesNotExist:
                username = None
        return super().authenticate(username, password)
