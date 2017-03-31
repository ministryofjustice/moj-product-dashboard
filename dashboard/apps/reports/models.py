# -*- coding: utf-8 -*-
from dashboard.apps.dashboard.models import Product


class ProductProxy(Product):
    class Meta(Product.Meta):
        permissions = (
            ('upload_payroll', 'Can upload monthly payroll'),
            ('adjustment_export', 'Can run Adjustment Export'),
            ('intercompany_export', 'Can run Intercompany Export'),
            ('productdetail_export', 'Can run Intercompany Export'),
        )
        app_label = 'reports'
        auto_created = True
        proxy = True
