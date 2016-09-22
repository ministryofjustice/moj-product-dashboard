# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

from django.test import TestCase
from model_mommy import mommy


from ..models import Product, Client, Person, PersonCost, Rate, Task
from ..constants import COST_TYPES
from ..forms import EXPORTS


class ExportTestCase(TestCase):
    fixtures = ['auth_group_permissions.yaml', 'test_users']

    def setUp(self):
        client = mommy.make(Client)
        self.product = mommy.make(Product, client=client)

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

    def test_can_export_files(self):
        self.client.login(username='test_finance', password='Admin123')
        for export in dict(EXPORTS).keys():
            response = self.client.post(
                '/admin/prototype/product/export/',
                {'date': date(2015, 1, 1), 'product': self.product.pk,
                 'export_type': export})
            self.assertEqual(response.status_code, 200)
