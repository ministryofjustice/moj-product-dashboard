# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime, date
from decimal import Decimal

from dateutil.rrule import rrule, MONTHLY
from extended_choices import Choices
import numpy as np

from .date_tools import get_workdays


RATE_TYPES = Choices(
    ('DAY',  1, 'Dayly rate'),
    ('MONTH',   2, 'Monthly salary'),
    ('YEAR', 3, 'Yearly salary'),
)


def dec_workdays(start_date, end_date):
    return Decimal(get_workdays(start_date, end_date))


class RateConverter():
    """
    RateConverter converts yearly salary and monthly salary to day rate
    """
    def __init__(self, rate, rate_type=RATE_TYPES.DAY):
        """
        param: rate: Decimal object
        param: rate_type: int object - one of RATE_TYPES
        """
        self.rate = rate
        self.rate_type = rate_type

    def _year_date_range(self, as_of):
        year = as_of.year
        return date(as_of.year, 1, 1), date(year, 12, 31)

    def _month_date_range(self, as_of):
        year = as_of.year
        month = as_of.month
        day, number = monthrange(year, month)
        return date(year, month, 1), date(year, month, number)

    def method_name(self, extension):
        return '_{}_{}'.format(
            RATE_TYPES.for_value(self.rate_type).constant.lower(),
            extension)

    @property
    def get_date_range(self):
        return getattr(self, self.method_name('date_range'))

    def average_day_rate(self, start_date=None, end_date=None, as_of=None):
        """
        Returns an average day rate over a time period
        #TODO: not implemented yet - returns day rate as of now()

        param: start_date: date object - beginning of time period for average
        param: end_date: date - object end of time period for average
        return: Decimal object - average day rate
        """
        if self.rate_type is RATE_TYPES.DAY:
            return self.rate

        if not start_date or not end_date:
            if not as_of:
                as_of = datetime.now()
            start_date, end_date = self.get_date_range(as_of)
            # No point continuing although would be same result
            return round(self.rate / dec_workdays(start_date, end_date), 2)

        total_workdays = dec_workdays(start_date, end_date)

        weights = []
        rates = []

        months = [dt.date() for dt in rrule(MONTHLY, dtstart=start_date,
                                            until=end_date)]
        # include last month
        months.append(date(end_date.year, end_date.month, 1))
        for n, start in enumerate(months):
            rate = self.rate / dec_workdays(*self.get_date_range(start))

            day, number = monthrange(start.year, start.month)
            end = date(start.year, start.month, number)

            if n is 0:
                start = start_date
            elif n + 1 is len(months):
                end = end_date

            # numpy won't average decimals
            # this seems close enough though
            weights.append(float(dec_workdays(start, end) / total_workdays))
            rates.append(float(rate))

        return round(Decimal(np.average(rates, weights=weights)), 2)


