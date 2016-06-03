#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tools for dealing with dates
"""
from datetime import datetime, timedelta
from functools import lru_cache

from numpy import busday_count
from pandas import date_range
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


def slice_time_window(start_date, end_date, freq):
    """
    slice a time window by frequency
    """
    dates = [ts.date() for ts in
             date_range(start_date, end_date, freq=freq)]
    if start_date not in dates:
        dates.insert(0, start_date)
    if end_date not in dates:
        dates.append(end_date + timedelta(days=1))
    time_windows = []
    for current_sd, next_sd in zip(dates, dates[1:]):
        current_ed = next_sd - timedelta(days=1)
        time_windows.append((current_sd, current_ed))
    return time_windows
