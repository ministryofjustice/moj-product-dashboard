from datetime import date
from dateutil.rrule import MONTHLY, YEARLY

from dashboard.libs.date_tools import (
    get_workdays, get_bank_holidays, get_overlap, parse,
    slice_time_window, dates_between)
import pytest


@pytest.mark.parametrize("start_date, end_date, expected", [
    ('2016-04-28', '2016-04-28', 1),  # same working day
    ('2016-04-30', '2016-04-30', 0),  # same weekend day
    ('2016-04-27', '2016-04-29', 3),  # just work days
    ('2016-04-27', '2016-04-30', 3),  # one weekend day
    ('2016-04-27', '2016-05-01', 3),  # two weekend days
    ('2016-04-27', '2016-05-02', 3),  # two weekend days plus a bank holiday
    ('2016-01-01', '2016-01-31', 20),  # Jan 2016
    ('2016-02-01', '2016-02-28', 20),  # Feb 2016
])
def test_get_work_days(start_date, end_date, expected):
    workdays = get_workdays(parse(start_date), parse(end_date))
    assert workdays == expected


@pytest.mark.parametrize("day", [
    '2015-12-28',  # boxing day (substitue day)
    '2016-05-02',  # may day
    '2016-05-30',  # spring bank holiday
    '2016-08-29',  # summer bank holiday (England)
    '2016-12-27',  # christmas day (substitue day)
])
def test_get_bank_holidays_good_days(day):
    assert parse(day) in get_bank_holidays(), \
        '{} is a bank holiday!'.format(day)


@pytest.mark.parametrize("day", [
    '2016-04-01',  # april fools day
    '2016-08-01',  # summer bank holiday (Scotland)
])
def test_get_bank_holidays_bad_days(day):
    assert parse(day) not in get_bank_holidays()


@pytest.mark.parametrize(
    "start_date0, end_date0, start_date1, end_date1, expected", [
        # no overlap
        ('2016-01-01', '2016-01-31', '2015-12-01', '2015-12-31', None),
        ('2015-12-01', '2015-12-31', '2016-01-01', '2016-01-31', None),
        # one time window is part of the other
        ('2015-12-01', '2016-01-31', '2015-12-31', '2016-01-01',
         ('2015-12-31', '2016-01-01')),
        # intersection is part of both time windows
        ('2015-12-01', '2016-01-01', '2015-12-31', '2016-01-31',
         ('2015-12-31', '2016-01-01')),
    ])
def test_get_overlap(start_date0, end_date0, start_date1, end_date1, expected):
    overlap = get_overlap((parse(start_date0), parse(end_date0)),
                          (parse(start_date1), parse(end_date1)))
    if expected:
        expected = parse(expected[0]), parse(expected[1])
    assert expected == overlap


# TODO more tests!
def test_slice_time_window():
    start_date = date(2015, 1, 2)
    end_date = date(2015, 12, 31)
    sliced = slice_time_window(start_date, end_date, 'MS')
    assert sliced[0] == (date(2015, 1, 2), date(2015, 1, 31))
    assert sliced[-1] == (date(2015, 12, 1), date(2015, 12, 31))


@pytest.mark.parametrize("start_date, end_date, frequency, expected", [
    (date(2015, 1, 2), date(2015, 3, 3), MONTHLY,
     [date(2015, 1, 2), date(2015, 2, 2), date(2015, 3, 2)]),

    (date(2015, 1, 31), date(2015, 3, 31), MONTHLY,
     [date(2015, 1, 31), date(2015, 2, 28), date(2015, 3, 31)]),

    (date(2015, 1, 29), date(2015, 3, 31), MONTHLY,
     [date(2015, 1, 29), date(2015, 2, 28), date(2015, 3, 29)]),

    (date(2015, 1, 2), date(2017, 3, 3), YEARLY,
     [date(2015, 1, 2), date(2016, 1, 2), date(2017, 1, 2)]),

    (date(2015, 1, 30), date(2017, 3, 3), YEARLY,
     [date(2015, 1, 30), date(2016, 1, 30), date(2017, 1, 30)]),
])
def test_slice_on_date(start_date, end_date, frequency, expected):
    dates = dates_between(start_date, end_date, frequency)
    assert dates == expected
