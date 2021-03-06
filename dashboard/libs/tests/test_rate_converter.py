# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from ..rate_converter import RateConverter, RATE_TYPES

DAY = RATE_TYPES.DAY
MONTH = RATE_TYPES.MONTH
YEAR = RATE_TYPES.YEAR


@pytest.mark.parametrize('on, rate, rate_type, expected', [
    (date(2016, 1, 1), '500', DAY, '500'),  # Day rate
    (date(2016, 1, 1), '4600', MONTH, '230'),  # Jan / 20 days
    (date(2016, 2, 1), '4600', MONTH, '219.05'),  # Feb / 21 days
    (date(2016, 3, 1), '4600', MONTH, '219.05'),  # Mar / 21 days
    (date(2016, 4, 1), '4600', MONTH, '219.05'),  # Apr / 21 days
    (date(2016, 5, 1), '4600', MONTH, '230'),  # May / 20 days
    (date(2016, 6, 1), '4600', MONTH, '209.09'),  # Jun / 22 days
    (date(2016, 7, 1), '4600', MONTH, '219.05'),  # Jul / 21 days
    (date(2016, 8, 1), '4600', MONTH, '209.09'),  # Aug / 22 days
    (date(2016, 9, 1), '4600', MONTH, '209.09'),  # Sep / 22 days
    (date(2016, 10, 1), '4600', MONTH, '219.05'),  # Oct / 21 days
    (date(2016, 11, 1), '4600', MONTH, '209.09'),  # Nov / 22 days
    (date(2016, 12, 1), '4600', MONTH, '230'),  # Dec / 20 days
    (date(2014, 1, 1), '60000', YEAR, '237.15'),  # 2014
    (date(2015, 1, 1), '60000', YEAR, '237.15'),  # 2015
    (date(2016, 1, 1), '60000', YEAR, '237.15'),  # 2016

    # use original values
    (date(2016, 1, 1), '500', DAY.original_value, '500'),
    (date(2016, 12, 1), '4600', MONTH.original_value, '230'),
    (date(2016, 1, 1), '60000', YEAR.original_value, '237.15'),

    (None, '4600', MONTH.original_value, '230'),
])
@patch('dashboard.libs.rate_converter.today')
def test_rate_at_certain_time(mock_today, on, rate, rate_type, expected):
    mock_today.return_value = date(2016, 1, 1)

    converter = RateConverter(Decimal(rate), rate_type)

    assert converter.rate_on(on=on) == Decimal(expected)


@pytest.mark.parametrize('start_date, end_date, rate, rate_type, expected', [
    ((2016, 4, 28), (2016, 4, 28), '500', DAY, '500'),  # Day rate
    ((2016, 1, 1), (2016, 1, 31), '4600', MONTH, '230'),  # Jan / 20 days
    ((2016, 2, 1), (2016, 2, 29), '4600', MONTH, '219.05'),  # Feb / 21 days
    ((2016, 3, 1), (2016, 3, 31), '4600', MONTH, '219.05'),  # Mar / 21 days
    ((2016, 4, 1), (2016, 4, 30), '4600', MONTH, '219.05'),  # Apr / 21 days
    ((2016, 5, 1), (2016, 5, 31), '4600', MONTH, '230'),  # May / 20 days
    ((2016, 6, 1), (2016, 6, 30), '4600', MONTH, '209.09'),  # Jun / 22 days
    ((2016, 7, 1), (2016, 7, 31), '4600', MONTH, '219.05'),  # Jul / 21 days
    ((2016, 8, 1), (2016, 8, 31), '4600', MONTH, '209.09'),  # Aug / 22 days
    ((2016, 9, 1), (2016, 9, 30), '4600', MONTH, '209.09'),  # Sep / 22 days
    ((2016, 10, 1), (2016, 10, 31), '4600', MONTH, '219.05'),  # Oct / 21 days
    ((2016, 11, 1), (2016, 11, 30), '4600', MONTH, '209.09'),  # Nov / 22 days
    ((2016, 12, 1), (2016, 12, 31), '4600', MONTH, '230'),  # Dec / 20 days
    ((2014, 1, 1), (2014, 12, 31), '60000', YEAR, '237.15'),  # 2014
    ((2015, 1, 1), (2015, 12, 31), '60000', YEAR, '237.15'),  # 2015
    ((2016, 1, 1), (2016, 12, 31), '60000', YEAR, '237.15'),  # 2016

    ((2016, 1, 4), (2016, 1, 4), '60000', YEAR, '237.15'),  # One day
    ((2016, 1, 4), (2016, 1, 4), '4600', MONTH, '230'),  # One day

    ((2016, 1, 28), (2016, 2, 2), '4600', MONTH, '224.52'),  # Equal days per month
    ((2016, 1, 28), (2016, 2, 3), '4600', MONTH, '223.43'),  # different amount of days in month
    ((2016, 1, 28), (2016, 6, 3), '4600', MONTH, '219.30'),  # multiple months
    ((2014, 1, 28), (2016, 2, 3), '4600', MONTH, '216.36'),  # multiple years
])
def test_cross_month_average(start_date, end_date, rate, rate_type, expected):
    converter = RateConverter(Decimal(rate), rate_type)

    assert converter.rate_between(
        start_date=date(*start_date),
        end_date=date(*end_date)) == Decimal(expected)
