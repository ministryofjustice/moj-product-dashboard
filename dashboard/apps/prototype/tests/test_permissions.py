# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.models import User, Group
from django.test import TestCase, mock

from model_mommy import mommy

from ..admin import (RateAdmin, Person, RateInline, ClientAdmin, ProjectAdmin,
                     TaskAdmin)
from ..models import Rate, Client, Project, Task


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
        mock_request = mock.Mock(user=user)
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

    def assertFieldsReadOnly(self, user, admin_class, model_class):
        mock_request = mock.Mock(user=user)
        model_admin = admin_class(model_class, admin.site)
        fields = [field.name for field in model_class._meta.fields]
        fields.remove('raw_data')
        self.assertListEqual(
            model_admin.get_readonly_fields(mock_request, model_class()),
            fields
        )

    def test_finance_can_access_rates(self):
        self.assertHasPermission(self.finance_admin, RateAdmin, Rate,
                                 delete=False)
        self.assertHasPermission(self.finance_admin, RateInline, Person,
                                 delete=False)

    def test_users_cant_access_rates(self):
        self.assertHasNoPermission(self.user_admin, RateAdmin, Rate)
        self.assertHasNoPermission(self.other_admin, RateAdmin, Rate)
        self.assertHasNoPermission(self.regular_user, RateAdmin, Rate)

        self.assertHasNoPermission(self.user_admin, RateInline, Person)
        self.assertHasNoPermission(self.other_admin, RateInline, Person)
        self.assertHasNoPermission(self.regular_user, RateInline, Person)

    def test_useradmin_can_access_users(self):
        self.assertHasPermission(self.user_admin, ModelAdmin, User)

    def test_users_cant_access_users(self):
        self.assertHasNoPermission(self.finance_admin, ModelAdmin, User)
        self.assertHasNoPermission(self.other_admin, ModelAdmin, User)
        self.assertHasNoPermission(self.regular_user, ModelAdmin, User)

    def test_read_only(self):
        self.assertHasPermission(self.finance_admin, ClientAdmin, Client,
                                 add=False, delete=False)
        self.assertHasPermission(self.finance_admin, ProjectAdmin, Project,
                                 add=False, delete=False)
        self.assertHasPermission(self.finance_admin, TaskAdmin, Task,
                                 add=False, delete=False)

    def test_read_only_fields(self):
        self.assertFieldsReadOnly(self.finance_admin, ClientAdmin, Client)
        self.assertFieldsReadOnly(self.finance_admin, TaskAdmin, Task)
