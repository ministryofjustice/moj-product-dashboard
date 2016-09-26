# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

from django.test import TestCase

from model_mommy import mommy

from dashboard.libs.rate_converter import RATE_TYPES
from ..models import Person, Rate


class RateTestCase(TestCase):
    def setUp(self):
        self.person = mommy.make(Person)

    def _add_rate(self, t, r, s):
        return Rate.objects.create(rate_type=t, rate=r, start_date=s,
                                   person=self.person)

    def assertDecimalEqual(self, dec, num_str, msg=None):
        self.assertEqual(dec, Decimal(num_str), msg)

    def test_rate_on(self):
        self._add_rate(RATE_TYPES.MONTH, 4600, date(2016, 5, 26))
        self._add_rate(RATE_TYPES.MONTH, 4800, date(2016, 5, 27))
        self._add_rate(RATE_TYPES.MONTH, 5000, date(2016, 5, 30))

        self.assertEqual(self.person.rate_on(date(2016, 5, 25)), None)
        self.assertDecimalEqual(self.person.rate_on(date(2016, 5, 26)), '230')
        self.assertDecimalEqual(self.person.rate_on(date(2016, 5, 27)), '240')
        self.assertDecimalEqual(self.person.rate_on(date(2016, 5, 30)), '250')

    def test_rate_between(self):
        self._add_rate(RATE_TYPES.MONTH, 4600, date(2016, 5, 26))
        self._add_rate(RATE_TYPES.MONTH, 4800, date(2016, 5, 27))
        self._add_rate(RATE_TYPES.MONTH, 5000, date(2016, 5, 30))

        self.assertEqual(self.person.rate_between(date(2016, 5, 24), date(2016, 5, 25)), None)
        self.assertDecimalEqual(self.person.rate_between(date(2016, 5, 24), date(2016, 5, 26)), '230')
        self.assertDecimalEqual(self.person.rate_between(date(2016, 5, 24), date(2016, 5, 27)), '235')
        self.assertDecimalEqual(self.person.rate_between(date(2016, 5, 24), date(2016, 5, 31)), '240')

        self.assertDecimalEqual(self.person.rate_between(date(2016, 5, 24), date(2020, 5, 30)), '229.61')

    def test_rate_string(self):
        rate = self._add_rate(RATE_TYPES.MONTH, 4600, date(2016, 5, 26))
        expected = '"{}" @ "4600 Monthly salary" from "2016-05-26"'.format(
            self.person.name)
        self.assertEquals(str(rate), expected)
