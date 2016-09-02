# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.test import TestCase

from dashboard.apps.prototype.permissions import user_is_finance


SWITCH_DM_TO_FINANCE_POST_DATA = {'is_staff': ['on'], 'date_joined_0':
                                  ['2016-05-20'],
                                  'date_joined_1': ['14:48:11'],
                                  'initial-date_joined_1': ['14:48:11'],
                                  'last_login_1': [''],
                                  '_continue': ['Save and continue editing'],
                                  'initial-date_joined_0': ['2016-05-20'],
                                  'groups': ['3', '2'], 'email': [''],
                                  'username': ['test_dm'],
                                  'last_login_0': [''], 'is_active': ['on'],
                                  'first_name': [''], 'last_name': ['']}


class ExportTestCase(TestCase):
    fixtures = ['auth_group_permissions.yaml', 'test_users']

    def setUp(self):
        finance_user = User.objects.get(pk=3)
        g = Group.objects.get(name='Admin')
        finance_user.groups.add(g)

    def test_admin_cant_switch_user_to_finance(self):
        self.client.login(username='test_admin', password='Admin123')

        response = self.client.post(
            '/admin/auth/user/4/change/',
            SWITCH_DM_TO_FINANCE_POST_DATA)
        self.assertEqual(response.status_code, 200)

        dm = User.objects.get(pk=4)
        self.assertFalse(user_is_finance(dm))

    def test_finance_can_switch_user_to_finance(self):
        self.client.login(username='test_finance', password='Admin123')

        response = self.client.post(
            '/admin/auth/user/4/change/',
            SWITCH_DM_TO_FINANCE_POST_DATA)
        self.assertEqual(response.status_code, 302)

        dm = User.objects.get(pk=4)
        self.assertTrue(user_is_finance(dm))
