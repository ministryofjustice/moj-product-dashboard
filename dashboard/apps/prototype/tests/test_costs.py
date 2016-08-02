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

    def test_cost_inside_range(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ONE_OFF,
            cost=Decimal('50')
        )

        self.assertEqual(
            cost.cost_between(date(2015, 1, 1), date(2015, 1, 2)),
            Decimal('50'))

    def test_rate_between(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.MONTHLY,
            cost=Decimal('3000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('142.86'))

    def test_rate_between_one_off(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ONE_OFF,
            cost=Decimal('3000')
        )

        self.assertRaises(
            Exception,
            cost.rate_between,
            date(2015, 1, 1),
            date(2015, 1, 2))

    def test_rate_between_anually(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('118.58'))

    def test_rate_between_anually_with_end(self):
        project = mommy.make(Project)
        cost = mommy.make(
            Cost,
            project=project,
            start_date=date(2015, 1, 1),
            end_date=date(2015, 6, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('291.26'))
