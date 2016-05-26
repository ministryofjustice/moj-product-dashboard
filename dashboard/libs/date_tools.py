#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tools for dealing with dates
"""
from datetime import datetime, timedelta
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
