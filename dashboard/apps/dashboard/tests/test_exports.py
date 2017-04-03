# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

from django.test import TestCase
from model_mommy import mommy


from dashboard.apps.dashboard.models import Product, Area, Person, PersonCost, Rate, Task
from dashboard.apps.dashboard.constants import COST_TYPES


class BaseExportTestCase(TestCase):
    fixtures = ['auth_group_permissions.yaml', 'test_users']

    def setUp(self):
        area = mommy.make(Area)
        self.product = mommy.make(Product, area=area)

        p = mommy.make(Person)
        c = mommy.make(Person, is_contractor=True)

        mommy.make(
            PersonCost,
            person=p,
            name='ASLC',
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        mommy.make(
            PersonCost,
            person=p,
            name='ASLC',
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        mommy.make(
            Rate,
            person=p,
            rate=1,
            start_date=date(2015, 1, 1)
        )

        mommy.make(
            Task,
            person=p,
            product=self.product,
            start_date=date(2015, 1, 1),
            end_date=date(2015, 1, 2),
            days=1
        )

        mommy.make(
            Rate,
            person=c,
            rate=1,
            start_date=date(2015, 1, 1)
        )

        mommy.make(
            Task,
            person=c,
            product=self.product,
            start_date=date(2015, 1, 1),
            end_date=date(2015, 1, 2),
            days=1
        )


class ExportTestCase(BaseExportTestCase):
    def test_can_export_products(self):
        for show in ['all', 'visible', self.product.pk]:
            response = self.client.get(
                '/products/export/%s/' % show)
            self.assertEqual(response.status_code, 200)

    def test_can_export_person_rates(self):
        self.client.login(username='test_dm', password='Admin123')
        response = self.client.get(
            '/admin/dashboard/products/export_rates/')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        self.client.login(username='test_finance', password='Admin123')
        response = self.client.get(
            '/admin/dashboard/person/export_rates/')
        self.assertEqual(response.status_code, 200)
