# -*- coding: utf-8 -*-
from datetime import date

from dashboard.apps.dashboard.tests.test_exports import BaseExportTestCase

from ..forms import EXPORTS


class ExportTestCase(BaseExportTestCase):
    def test_can_export_files(self):
        self.client.login(username='test_finance', password='Admin123')
        for export in dict(EXPORTS).keys():
            response = self.client.post(
                '/admin/reports/report/export/',
                {'date': date(2015, 1, 1), 'product': self.product.pk,
                 'export_type': export})
            self.assertEqual(response.status_code, 200)
