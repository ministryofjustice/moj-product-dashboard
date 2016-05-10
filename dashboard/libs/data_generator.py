#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data generator for dashboard graphs
"""
from datetime import datetime, timedelta
from collections import OrderedDict

import pandas as pd
import numpy as np


def gen_forcast():
    forecast = OrderedDict()
    start_date = datetime.now() - timedelta(days=30 * 6)
    periods = pd.period_range(start_date.strftime('%Y-%m-%d'),
                              periods=18, freq='M')
    for p in periods:
        val = np.random.uniform(4, 6)
        forecast[p] = OrderedDict([
            ('Civil Servant', val),
            ('Contractor', val * np.random.uniform(0.7, 1))
        ])
    return forecast


def gen_project_timeline():
    timeline = {
        'discovery': {'date': '2015-04-10', },
        'alpha': {'date': '2015-08-10', },
        'beta': {'date': '2016-01-20', },
        'live': {'date': '2016-07-28', },
        'project end': {'date': '2016-09-15', },
    }
    for value in timeline.values():
        value['date'] = datetime.strptime(value['date'], '%Y-%m-%d')
    return timeline


def gen_monthly_spendings():
    spendings = OrderedDict()
    now = datetime.now()
    start_date = now - timedelta(days=30 * 9)
    periods = pd.period_range(start_date.strftime('%Y-%m-%d'),
                              periods=12, freq='M')
    for p in periods:
        forcast = np.random.uniform(80, 120)
        if p.year > now.year or (p.year == now.year and p.month >= now.month):
            actual = 0
        else:
            actual = forcast * np.random.uniform(0.7, 1)
        spendings[p] = OrderedDict([
            ('Actual', actual),
            ('Forecast', forcast)
        ])
    return spendings
