#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tools for dealing with dates
"""
from datetime import timedelta
from functools import lru_cache

import requests

BANK_HOLIDAY_URL = 'https://www.gov.uk/bank-holidays/england-and-wales.json'


@lru_cache()
def get_bank_holidays():
    """
    get bank holiday data from gov.uk
    :return: a dictionary of bank holidays with the date as key and more
    details as value
    """
    response = requests.get(BANK_HOLIDAY_URL)
    response.raise_for_status()
    return {event['date']: event for event in response.json()['events']}


def get_workdays(start_date, end_date):
    """
    get number of workdays in a date span
    :param start_date: date object for the start date
    :param end_date: date object for the end date
    :return: an integer for the number of work days
    """
    days = (start_date + timedelta(i) for i in
            range((end_date - start_date).days + 1))
    bank_holidays = get_bank_holidays()
    workdays = [
        d for d in days if
        d.weekday() < 5 and d.strftime('%Y-%m-%d') not in bank_holidays]
    return len(workdays)
