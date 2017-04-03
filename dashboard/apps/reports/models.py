# -*- coding: utf-8 -*-
from dashboard.apps.dashboard.models import Product


class Report(Product):
    class Meta(Product.Meta):
        app_label = 'reports'
        auto_created = True
        proxy = True
