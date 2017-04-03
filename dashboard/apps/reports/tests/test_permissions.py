# -*- coding: utf-8 -*-
from urllib.request import Request

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.test import mock

from dashboard.apps.dashboard.tests.test_permissions import BasePermissionTestCase

from reports.admin import ReportsAdmin
from reports.models import Report


class RatePermissionTestCase(BasePermissionTestCase):

    fixtures = ['auth_group_permissions.yaml']

    def test_upload_permission(self):
        mock_request = mock.Mock(user=self.finance_admin)
        model_admin = ReportsAdmin(Report, admin.site)
        can_upload = model_admin.has_upload_permission(mock_request)
        self.assertTrue(can_upload)
        self.assertDictEqual(model_admin.get_model_perms(mock_request), {
            'add': False, 'change': False, 'delete': False, 'upload': True,
            'export': True})

        mock_request = mock.Mock(user=self.super_user)
        can_upload = model_admin.has_upload_permission(mock_request)
        self.assertFalse(can_upload)

    def test_users_cant_access_exports(self):
        model_admin = ReportsAdmin(Report, admin.site)
        for user in [self.user_admin, self.other_admin, self.regular_user]:
            mock_request = mock.Mock(user=user)

            self.assertRaises(
                PermissionDenied,
                model_admin.export_view,
                mock_request)

    def test_finance_users_can_access_exports(self):
        model_admin = ReportsAdmin(Report, admin.site)
        mock_request = mock.Mock(spec=Request, user=self.finance_admin,
                                 method='GET', COOKIES={}, META={})

        resp = model_admin.export_view(mock_request)
        self.assertEqual(resp.status_code, 200)
