# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import User, Group
from django.test import TestCase

from model_mommy import mommy

from ..admin import RateAdmin
from ..models import Rate


class MockRequest():
    def __init__(self, user):
        self.user = user


class TaskTimeSpentTestCase(TestCase):

    fixtures = ['auth_group_permissions.yaml']

    def setUp(self):
        self.super_user = mommy.make(User, is_superuser=True, is_active=True)

        self.finance_admin = mommy.make(User, is_staff=True, is_active=True)
        self.finance_admin.groups.add(Group.objects.get(name='Finance'))

        self.user_admin = mommy.make(User, is_staff=True, is_active=True)
        self.user_admin.groups.add(Group.objects.get(name='Admin'))

        self.other_admin = mommy.make(User, is_staff=True, is_active=True)

        self.regular_user = mommy.make(User, is_active=True)

    def assertHasPermission(self, user, admin_class, model_class, add=True,
                            change=True, delete=True):
        mock_request = MockRequest(user=user)
        model_admin = admin_class(model_class, admin.site)
        can_add = model_admin.has_add_permission(mock_request)
        can_change = model_admin.has_change_permission(mock_request)
        can_delete = model_admin.has_delete_permission(mock_request)
        self.assertEqual(add, can_add, 'Add permissions incorrect')
        self.assertEqual(change, can_change, 'Change permissions incorrect')
        self.assertEqual(delete, can_delete, 'Delete permissions incorrect')

    def assertHasNoPermission(self, user, admin_class, model_class):
        self.assertHasPermission(user, admin_class, model_class,
                                 add=False, change=False, delete=False)

    def test_finance_can_access_rates(self):
        self.assertHasPermission(self.finance_admin, RateAdmin, Rate,
                                 delete=False)

    def test_users_cant_access_rates(self):
        self.assertHasNoPermission(self.user_admin, RateAdmin, Rate)
        self.assertHasNoPermission(self.other_admin, RateAdmin, Rate)
        self.assertHasNoPermission(self.regular_user, RateAdmin, Rate)

    def test_useradmin_can_access_users(self):
        self.assertHasPermission(self.user_admin, ModelAdmin, User)

    def test_users_cant_access_users(self):
        self.assertHasNoPermission(self.finance_admin, ModelAdmin, User)
        self.assertHasNoPermission(self.other_admin, ModelAdmin, User)
        self.assertHasNoPermission(self.regular_user, ModelAdmin, User)
