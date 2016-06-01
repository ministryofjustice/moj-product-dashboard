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
    """
    Returns workdays in Decimal
    :param start_date: date object
    :param end_date: date object
    :return: Decimal object - number of workdays between
    """
    return Decimal(get_workdays(start_date, end_date))


def last_date_in_month(d):
    """
    Returns the date of the last day in the month
    :param d: date object
    :return: date object = last day of month
    """
    day, number = monthrange(d.year, d.month)
    return date(d.year, d.month, number)


def month_segments(converter, start_date, end_date):
    """
    Split in to segments of months between start_date and end_date
    :param converter: RateConverter object
    :param start_date: date object - start date of segments
    :param end_date: date object - end date of segments
    :return: list of tuples with (start, end, rate) for each month
    """
    def rate(d):
        return converter.rate / dec_workdays(*converter.get_date_range(d))

    months = [(dt.date(), last_date_in_month(dt), rate(dt.date())) for dt in
              rrule(MONTHLY, dtstart=start_date, until=end_date)]
    # include last month
    months.append(
        (date(end_date.year, end_date.month, 1), end_date, rate(end_date))
    )
    return months


def average_rate_from_segments(segments, total_workdays):
    """
    Returns average rate for a list of date segments
    :param segments: list of tuples (start (date object), end (date object),
                                    rate (Decimal object))
    :param total_workdays: total number of workdays to average over
    :return: Decimal object - average day rate over segments
    """
    if total_workdays:
        weights = []
        rates = []

        for start, end, rate in segments:
            # numpy won't average decimals
            # this seems close enough though
            weight = dec_workdays(start, end) / total_workdays
            if weight:
                weights.append(float(weight))
                rates.append(float(rate))

        if rates and weights:
            return round(Decimal(np.average(rates, weights=weights)), 2)


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

    def _year_date_range(self, on):
        """
        Returns dated for beginning and end of year
        :param on: date object
        :return: tuple object - beginning and end of year
        """
        year = on.year
        return date(on.year, 1, 1), date(year, 12, 31)

    def _month_date_range(self, on):
        """
        Returns dated for beginning and end of month
        :param on: date object
        :return: tuple object - beginning and end of month
        """
        year = on.year
        month = on.month
        return date(year, month, 1), last_date_in_month(on)

    @property
    def range_method(self):
        return '_{}_date_range'.format(
            RATE_TYPES.for_value(self.rate_type).constant.lower())

    @property
    def get_date_range(self):
        return getattr(self, self.range_method)

    def rate_on(self, on=None):
        """
        Returns an average day rate over a time period

        param: start_date: date object - beginning of time period for average
        param: end_date: date - object end of time period for average
        return: Decimal object - average day rate
        """
        if self.rate_type == RATE_TYPES.DAY:
            return self.rate

        if not on:
            on = datetime.now()
        start_date, end_date = self.get_date_range(on)
        # No point continuing although would be same result
        return round(self.rate / dec_workdays(start_date, end_date), 2)

    def rate_between(self, start_date, end_date):
        """
        Returns an average day rate over a time period

        param: start_date: date object - beginning of time period for average
        param: end_date: date - object end of time period for average
        return: Decimal object - average day rate
        """
        if self.rate_type == RATE_TYPES.DAY:
            return self.rate

        total_workdays = dec_workdays(start_date, end_date)
        segments = month_segments(self, start_date, end_date)

        return average_rate_from_segments(segments, total_workdays)
