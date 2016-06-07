# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from django.test import TestCase

from model_mommy import mommy

from ..constants import COST_TYPES
from ..models import Cost, Project


class CostTestCase(TestCase):

    def test_zero_cost_outside_range(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ONE_OFF,
            cost=Decimal('50')
        )

        self.assertEqual(
            cost.cost_between(date(2015, 1, 2), date(2015, 1, 3)),
            Decimal('0'))
