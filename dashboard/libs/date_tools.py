#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tools for dealing with dates
"""
from datetime import date, datetime, timedelta
from dateutil.rrule import rrule, MONTHLY
from functools import lru_cache

from numpy import busday_count
from pandas import date_range
import requests

BANK_HOLIDAY_URL = 'https://www.gov.uk/bank-holidays/england-and-wales.json'


def parse_date(date_string, format='%Y-%m-%d'):
    """
    parse a date string
    :param date_string: a string representing a date
    :param format: format of the string, default to '%Y-%m-%d'
    :return: a date object
    """
    return datetime.strptime(date_string, format).date()


def to_datetime(date):
    """
    convert a date object to datetime object
    :param date: a date object
    :return: a datetime object
    """
    return datetime(*date.timetuple()[:6])


@lru_cache()
def get_bank_holidays():
    """
    get bank holiday data from gov.uk
    :return: a dictionary of bank holidays with the date as key and more
    details as value
    """
    response = requests.get(BANK_HOLIDAY_URL)
    response.raise_for_status()
    return [parse_date(event['date']) for event in response.json()['events']]


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
    """
    get a list of workdays in a time window defined by start date and end date
    :param start_date: date object for the start date
    :param end_date: date object for the end date
    :return: a list of date objects
    """
    days = (start_date + timedelta(i) for i in
            range((end_date - start_date).days + 1))
    bank_holidays = get_bank_holidays()
    workdays = [
        d for d in days if
        d.weekday() < 5 and d not in bank_holidays]

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


def slice_time_window(start_date, end_date, freq, extend=False):
    """
    slice a time window by frequency
    :param start_date: start of the time window
    :param end_date: end of the time window
    :param freq: frequency string is an offset aliases supported by pandas
    :param extend: a boolean value. if it's true, the start_date and end_date
    will be extended to the previous and next value following the frequency.
    for example, if the freqency is 'MS', the start date is 2016/01/03,
    end date 2016/12/25, it will be extended to 2016/01/01 - 2017/01/01
    :return: a list of tuples
    """
    end_date = end_date + timedelta(days=1)
    if extend:
        start_date = date_range(end=start_date, periods=1, freq=freq)[0].date()
        end_date = date_range(start=end_date, periods=1, freq=freq)[0].date()
    dates = [ts.date() for ts in date_range(start_date, end_date, freq=freq)]
    if start_date not in dates:
        dates.insert(0, start_date)
    if end_date not in dates:
        dates.append(end_date)
    time_windows = []
    for current_sd, next_sd in zip(dates, dates[1:]):
        current_ed = next_sd - timedelta(days=1)
        time_windows.append((current_sd, current_ed))
    return time_windows


def dates_between(start_date, end_date, freq, bymonthday=None, bysetpos=None,
                  byyearday=None):
    """
    returns list of dates of freq (MONTHLY, YEARLY) between two dates
    :param start_date: date object - date to start on
    :param end_date:  date object - date to end on
    :param freq: int object - dateutil.rrule constant
    :param bymonthday: int or list of ints - see rrule
    :param bysetpos: int or list of ints - see rrule
    :return: list object - list of date objects
    """
    if bymonthday and bymonthday > 28 and freq == MONTHLY:
        bymonthday = range(28, bymonthday + 1)
        bysetpos = -1
    return [dt.date() for dt in
            rrule(freq, dtstart=start_date, until=end_date,
                  bymonthday=bymonthday, bysetpos=bysetpos,
                  byyearday=byyearday)]


def financial_year_tuple(year):
    return date(year, 4, 6), date(year + 1, 4, 5)
