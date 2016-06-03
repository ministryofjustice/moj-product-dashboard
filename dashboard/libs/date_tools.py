#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tools for dealing with dates
"""
from datetime import datetime, timedelta, date
from calendar import monthrange, month_abbr, month_name
from functools import lru_cache

from numpy import busday_count
import requests

BANK_HOLIDAY_URL = 'https://www.gov.uk/bank-holidays/england-and-wales.json'


def parse(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d').date()


@lru_cache()
def get_bank_holidays():
    """
    get bank holiday data from gov.uk
    :return: a dictionary of bank holidays with the date as key and more
    details as value
    """
    response = requests.get(BANK_HOLIDAY_URL)
    response.raise_for_status()
    return [parse(event['date']) for event in response.json()['events']]


def get_workdays(start_date, end_date):
    """
    get number of workdays in a date span
    :param start_date: date object for the start date
    :param end_date: date object for the end date
    :return: an integer for the number of work days
    """
    days = int(busday_count(start_date, end_date + timedelta(days=1),
                            holidays=get_bank_holidays()))
    return max(0, days)


def get_workdays_list(start_date, end_date):
    days = (start_date + timedelta(i) for i in
            range((end_date - start_date).days + 1))
    bank_holidays = get_bank_holidays()
    workdays = [
        d for d in days if
        d.weekday() < 5 and d.strftime('%Y-%m-%d') not in bank_holidays]

    return workdays


def get_overlap(time_window0, time_window1):
    """
    get the overlap of two time windows
    :param time_window0: a tuple of date/datetime objects represeting the
    start and end of a time window
    :param time_window1: a tuple of date/datetime objects represeting the
    start and end of a time window
    :return: a tuple of date/datetime objects represeting the start and
    end of a time window or None if no overlapping found
    :raise: ValueError
    """
    sdate0, edate0 = time_window0
    sdate1, edate1 = time_window1

    error = 'start date {} is greater than end date {}'
    if edate0 < sdate0:
        raise ValueError(error.format(sdate0, edate0))
    if edate1 < sdate1:
        raise ValueError(error.format(sdate1, edate1))

    if sdate1 < sdate0:
        if edate1 < sdate0:
            overlap = None
        elif edate1 <= edate0:
            overlap = sdate0, edate1
        else:
            overlap = sdate0, edate0
    elif sdate1 <= edate0:
        if edate1 <= edate0:
            overlap = sdate1, edate1
        else:
            overlap = sdate1, edate0
    else:
        overlap = None
    return overlap


def get_time_windows(start_date, end_date, increment='month'):
    """
    get a list of paired start and end dates
    :param start_date: the start date for the overall period
    :param end_date: the end date for the overall period
    :param increment: day, week or month
    :return: a list of lists, each with two date objects
    """
    time_windows = []

    if increment == 'month':

        if start_date.day != 1:
            start_date = date(start_date.year, start_date.month, 1)

        while start_date < end_date:
            month_range = [start_date,
                           date(start_date.year, start_date.month, monthrange(start_date.year,
                                                                              start_date.month)[1]),
                           '%s %s' % (month_abbr[start_date.month], str(start_date.year))]

            time_windows.append(month_range)
            start_date = month_range[1] + timedelta(days=1)

    elif increment == 'week':

        if start_date.isoweekday() != 1:
            start_date = start_date - timedelta(days=start_date.isoweekday() - 1)

        while start_date < end_date:
            week_range = [start_date,
                          start_date + timedelta(days=6),
                          'w/c %s/%s/%s' % (str(start_date.day), month_abbr[start_date.month], str(start_date.year))]

            time_windows.append(week_range)
            start_date = week_range[1] + timedelta(days=1)

    elif increment == 'day':

        while start_date <= end_date:
            day_range = [start_date,
                         start_date,
                         '%s/%s/%s' % (str(start_date.day), str(start_date.month), str(start_date.year))]

            time_windows.append(day_range)
            start_date = day_range[1] + timedelta(days=1)

    return time_windows
