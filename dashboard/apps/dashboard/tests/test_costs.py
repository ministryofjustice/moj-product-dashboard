# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

from django.test import TestCase
from model_mommy import mommy
import pytest

from ..constants import COST_TYPES
from ..forms import PAYROLL_COSTS
from ..models import Cost, Product, Person, PersonCost, Rate, Task


class CostTestCase(TestCase):

    def test_zero_cost_outside_range(self):
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ONE_OFF,
            cost=Decimal('50')
        )

        self.assertEqual(
            cost.cost_between(date(2015, 1, 2), date(2015, 1, 3)),
            Decimal('0'))

    def test_cost_inside_range(self):
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ONE_OFF,
            cost=Decimal('50')
        )

        self.assertEqual(
            cost.cost_between(date(2015, 1, 1), date(2015, 1, 2)),
            Decimal('50'))

    def test_rate_between(self):
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.MONTHLY,
            cost=Decimal('3000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('142.86'))

        self.assertEqual(
            round(cost.rate_between(date(2014, 1, 1), date(2014, 1, 2)), 2),
            Decimal('0'))

        self.assertEqual(
            round(cost.rate_between(date(2014, 1, 1), date(2014, 1, 2)), 2),
            Decimal('0'))

    def test_rate_between_one_off(self):
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
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
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
            start_date=date(2015, 1, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('118.58'))

    def test_rate_between_anually_with_end(self):
        product = mommy.make(Product)
        cost = mommy.make(
            Cost,
            product=product,
            start_date=date(2015, 1, 1),
            end_date=date(2015, 6, 1),
            type=COST_TYPES.ANNUALLY,
            cost=Decimal('30000')
        )

        self.assertEqual(
            round(cost.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('291.26'))

    def test_monthly_person_cost(self):
        start_date = date(2016, 9, 1)
        end_date = date(2016, 9, 30)

        p = mommy.make(Person)

        r = mommy.make(
            Rate,
            person=p,
            rate=1,
            start_date=start_date
        )

        for payrol_cost in PAYROLL_COSTS:
            pc = mommy.make(
                PersonCost,
                person=p,
                name=payrol_cost,
                start_date=start_date,
                type=COST_TYPES.MONTHLY,
                cost=Decimal('1')
            )
            self.assertEqual(pc.rate_between(start_date, end_date),
                             Decimal('0.04545454545454545454545454545'))

        total_cost = (len(PAYROLL_COSTS) * Decimal('1') + r.rate * 22) / 22

        self.assertEqual(round(p.rate_between(start_date, end_date), 8),
                         round(total_cost, 8))

    def test_rate_between_anually_with_person_cost(self):
        proj = mommy.make(Product)
        p = mommy.make(Person)

        pc = mommy.make(
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
            product=proj,
            start_date=date(2015, 1, 1),
            end_date=date(2015, 1, 2),
            days=1
        )

        self.assertEqual(
            round(pc.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('118.58'))

        self.assertEqual(
            round(proj.people_additional_costs(date(2015, 1, 1), date(2015, 1, 2), 'ASLC'), 2),
            Decimal('118.58'))

        self.assertEqual(
            round(proj.people_additional_costs(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('118.58'))

        self.assertEqual(
            round(p.rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('119.58'))

        self.assertEqual(
            round(p.base_rate_between(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('1'))

        self.assertEqual(
            round(p.additional_rate(date(2015, 1, 1), date(2015, 1, 2)), 2),
            Decimal('118.58'))

        self.assertEqual(
            round(p.additional_rate(date(2015, 1, 1), date(2015, 1, 2), 'ASLC'), 2),
            Decimal('118.58'))


@pytest.mark.parametrize("start_date, end_date", [
    (date(2015, 5, 1), date(2015, 5, 1)),
    (date(2015, 5, 1), date(2015, 5, 15)),
    (date(2015, 5, 1), date(2015, 5, 31)),
    (date(2015, 5, 1), date(2015, 6, 1)),
    (date(2015, 5, 1), date(2015, 6, 15)),
    (date(2015, 5, 1), date(2015, 6, 30)),

    (date(2015, 5, 15), date(2015, 6, 15)),
    (date(2015, 5, 31), date(2015, 6, 30)),
    (date(2015, 5, 31), date(2015, 6, 1)),

    (date(2015, 6, 1), date(2015, 6, 1)),
    (date(2015, 6, 1), date(2015, 6, 15)),
    (date(2015, 6, 1), date(2015, 6, 30)),
])
@pytest.mark.django_db
def test_person_cost_prediction(start_date, end_date):
    rate = Decimal('50')
    p = mommy.make(Person)

    mommy.make(
        PersonCost,
        person=p,
        name='ASLC',
        start_date=date(2015, 5, 1),
        end_date=date(2015, 5, 31),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('950')
    )
    mommy.make(
        Rate,
        person=p,
        start_date=date(2015, 5, 1),
        rate_type=COST_TYPES.MONTHLY,
        rate=Decimal('2000')
    )

    assert rate == p.additional_rate(
        start_date, end_date, predict_based_on=date(2015, 5, 31))
