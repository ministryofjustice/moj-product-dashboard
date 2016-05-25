from datetime import datetime

from dashboard.libs.date_tools import get_workdays, get_bank_holidays
import pytest


@pytest.mark.parametrize("start_date, end_date, expected", [
    ('2016-04-28', '2016-04-28', 1),  # same working day
    ('2016-04-30', '2016-04-30', 0),  # same weekend day
    ('2016-04-27', '2016-04-29', 3),  # just work days
    ('2016-04-27', '2016-04-30', 3),  # one weekend day
    ('2016-04-27', '2016-05-01', 3),  # two weekend days
    ('2016-04-27', '2016-05-02', 3),  # two weekend days plus a bank holiday
])
def test_get_work_days(start_date, end_date, expected):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    workdays = get_workdays(start_date, end_date)
    assert workdays == expected


@pytest.mark.parametrize("day", [
    '2015-12-28',  # boxing day (substitue day)
    '2016-05-02',  # may day
    '2016-05-30',  # spring bank holiday
    '2016-08-29',  # summer bank holiday (England)
    '2016-12-27',  # christmas day (substitue day)
])
def test_get_bank_holidays_good_days(day):
    assert datetime.strptime(day, '%Y-%m-%d').date() in get_bank_holidays(), \
        '{} is a bank holiday!'.format(day)


@pytest.mark.parametrize("day", [
    '2016-04-01',  # april fools day
    '2016-08-01',  # summer bank holiday (Scotland)
])
def test_get_bank_holidays_bad_days(day):
    assert datetime.strptime(day, '%Y-%m-%d').date() not in \
           get_bank_holidays()
