# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

import pytest

from ..rate_converter import RateConverter, RATE_TYPES


@pytest.mark.parametrize('on, rate, rate_type, expected', [
    (date(2016, 1, 1), '500', RATE_TYPES.DAY, '500'),  # Day rate
    (date(2016, 1, 1), '4600', RATE_TYPES.MONTH, '230'),  # Jan / 20 days
    (date(2016, 2, 1), '4600', RATE_TYPES.MONTH, '219.05'),  # Feb / 21 days
    (date(2016, 3, 1), '4600', RATE_TYPES.MONTH, '219.05'),  # Mar / 21 days
    (date(2016, 4, 1), '4600', RATE_TYPES.MONTH, '219.05'),  # Apr / 21 days
    (date(2016, 5, 1), '4600', RATE_TYPES.MONTH, '230'),  # May / 20 days
    (date(2016, 6, 1), '4600', RATE_TYPES.MONTH, '209.09'),  # Jun / 22 days
    (date(2016, 7, 1), '4600', RATE_TYPES.MONTH, '219.05'),  # Jul / 21 days
    (date(2016, 8, 1), '4600', RATE_TYPES.MONTH, '209.09'),  # Aug / 22 days
    (date(2016, 9, 1), '4600', RATE_TYPES.MONTH, '209.09'),  # Sep / 22 days
    (date(2016, 10, 1), '4600', RATE_TYPES.MONTH, '219.05'),  # Oct / 21 days
    (date(2016, 11, 1), '4600', RATE_TYPES.MONTH, '209.09'),  # Nov / 22 days
    (date(2016, 12, 1), '4600', RATE_TYPES.MONTH, '230'),  # Dec / 20 days
    (date(2014, 1, 1), '60000', RATE_TYPES.YEAR, '237.15'),  # 2014
    (date(2015, 1, 1), '60000', RATE_TYPES.YEAR, '237.15'),  # 2015
    (date(2016, 1, 1), '60000', RATE_TYPES.YEAR, '237.15'),  # 2016
])
def test_rate_at_certain_time(on, rate, rate_type, expected):
    converter = RateConverter(Decimal(rate), rate_type)

    assert converter.rate_on(on=on) == Decimal(expected)


@pytest.mark.parametrize('start_date, end_date, rate, rate_type, expected', [
    (date(2016, 4, 28), date(2016, 4, 28), '500', RATE_TYPES.DAY, '500'),  # Day rate
    (date(2016, 1, 1), date(2016, 1, 31), '4600', RATE_TYPES.MONTH, '230'),  # Jan / 20 days
    (date(2016, 2, 1), date(2016, 2, 29), '4600', RATE_TYPES.MONTH, '219.05'),  # Feb / 21 days
    (date(2016, 3, 1), date(2016, 3, 31), '4600', RATE_TYPES.MONTH, '219.05'),  # Mar / 21 days
    (date(2016, 4, 1), date(2016, 4, 30), '4600', RATE_TYPES.MONTH, '219.05'),  # Apr / 21 days
    (date(2016, 5, 1), date(2016, 5, 31), '4600', RATE_TYPES.MONTH, '230'),  # May / 20 days
    (date(2016, 6, 1), date(2016, 6, 30), '4600', RATE_TYPES.MONTH, '209.09'),  # Jun / 22 days
    (date(2016, 7, 1), date(2016, 7, 31), '4600', RATE_TYPES.MONTH, '219.05'),  # Jul / 21 days
    (date(2016, 8, 1), date(2016, 8, 31), '4600', RATE_TYPES.MONTH, '209.09'),  # Aug / 22 days
    (date(2016, 9, 1), date(2016, 9, 30), '4600', RATE_TYPES.MONTH, '209.09'),  # Sep / 22 days
    (date(2016, 10, 1), date(2016, 10, 31), '4600', RATE_TYPES.MONTH, '219.05'),  # Oct / 21 days
    (date(2016, 11, 1), date(2016, 11, 30), '4600', RATE_TYPES.MONTH, '209.09'),  # Nov / 22 days
    (date(2016, 12, 1), date(2016, 12, 31), '4600', RATE_TYPES.MONTH, '230'),  # Dec / 20 days
    (date(2014, 1, 1), date(2014, 12, 31), '60000', RATE_TYPES.YEAR, '237.15'),  # 2014
    (date(2015, 1, 1), date(2015, 12, 31), '60000', RATE_TYPES.YEAR, '237.15'),  # 2015
    (date(2016, 1, 1), date(2016, 12, 31), '60000', RATE_TYPES.YEAR, '237.15'),  # 2016

    (date(2016, 1, 4), date(2016, 1, 4), '60000', RATE_TYPES.YEAR, '237.15'),  # One day
    (date(2016, 1, 4), date(2016, 1, 4), '4600', RATE_TYPES.MONTH, '230'),  # One day

    (date(2016, 1, 28), date(2016, 2, 2), '4600', RATE_TYPES.MONTH, '224.52'),  # Equal days per month
    (date(2016, 1, 28), date(2016, 2, 3), '4600', RATE_TYPES.MONTH, '223.43'),  # different amount of days in month
    (date(2016, 1, 28), date(2016, 6, 3), '4600', RATE_TYPES.MONTH, '219.30'),  # multiple months
    (date(2014, 1, 28), date(2016, 2, 3), '4600', RATE_TYPES.MONTH, '216.36'),  # multiple years
])
def test_cross_month_average(start_date, end_date, rate, rate_type, expected):
    converter = RateConverter(Decimal(rate), rate_type)

    assert converter.rate_between(
        start_date=start_date,
        end_date=end_date) == Decimal(expected)
