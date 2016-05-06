# -*- coding: utf-8 -*-
import datetime

from django.shortcuts import render

import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.models import Range1d
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.charts import Bar, Line
from bokeh.charts.attributes import  CatAttr
from bokeh.models import (
    PrintfTickFormatter, NumeralTickFormatter, DatetimeTickFormatter)


STYLE= {
    'plot_width': 400,
    'plot_height': 200,
    'responsive': True,
    'logo': None,
    'xlabel': '',
    'ylabel': '',
    'toolbar_location': 'above',
}

def bar_group():
    months = ['Mar 2016', 'Apr 2016', 'May 2016', 'June 2016']
    data = {
        'months': sum([[m, m] for m in months], []),
        'keys': ['Actual', 'Forecast'] * 4,
        'spendings': [80, 120,
                      90, 140,
                      0, 100,
                      0, 100,]
    }
    label = CatAttr(columns='months', sort=False)
    bar = Bar(data, values='spendings', label=label, group='keys',
              color=['dodgerblue', 'lightblue'],
              agg='median', title="Monthly Spend",
              legend='top_right', **STYLE)
    # TODO this does not feel right, but bokeh doesn't present
    # a better way to do it.
    bar._yaxis.formatter = PrintfTickFormatter(format='£%dk')
    return bar


def line():
    xyvalues = np.array([[2, 7, 15, 20, 26],])

    line = Line(xyvalues, title="Cumulative Spend", legend="top_left",
                **STYLE)
    return line


def bar_stack():
    months = ['Mar 2016', 'Apr 2016', 'May 2016', 'June 2016']
    data = {
        'months': sum([[m, m] for m in months], []),
        'keys': ['Civil Servants', 'Contractors'] * 4,
        'spendings': [3, 0.5,
                      6, 3.5,
                      6, 3.5,
                      4, 4,]
    }
    label = CatAttr(columns='months', sort=False)
    bar = Bar(data, values='spendings', label=label, stack='keys',
              color=['dodgerblue', 'lightblue'],
              title="Forecast FTE Civil Servant/Contractor split",
              legend='top_right', **STYLE)
    # TODO this does not feel right, but bokeh doesn't present
    # a better way to do it.
    bar._yaxis.formatter = NumeralTickFormatter(format='0.00')
    return bar


def timeline():
    x = [datetime.date(year=period.year, month=period.month, day=1)
         for period in pd.period_range('2015-01', periods=24, freq='M')]
    p = figure(title='Timeline', plot_width=400,
               plot_height=150, responsive=True,
               x_axis_type="datetime", y_range=(-2, 8), logo=None)
    p.line(x=x, y=[0] * len(x))
    p.yaxis.visible= None
    p.ygrid.grid_line_color = None
    p.outline_line_color = None
    p.xaxis.formatter = DatetimeTickFormatter(formats=dict(
        days=["%b %y"], 
        months=["%b %y"],
        years=["%b %y"], 
    ))
    p.diamond([datetime.date(2015, 4, 10)], [0], size=10, color="olive", alpha=0.5, legend="discovery")
    p.diamond([datetime.date(2015, 8, 10)], [0], size=10, color="navy", alpha=0.5, legend="alpha")
    p.diamond([datetime.date(2016, 1, 20)], [0], size=10, color="red", alpha=0.5, legend="beta")
    p.diamond([datetime.date(2016, 7, 28)], [0], size=10, color="green", alpha=0.5, legend="live")
    p.diamond([datetime.date(2016, 9, 15)], [0], size=10, color="blue", alpha=0.5, legend="project end")
    p.circle([datetime.date.today()], [0], size=10, color="black", alpha=0.5, legend="today")
    p.legend.orientation = 'top_left'
    p.legend.background_fill_alpha = 0.5
    return p
    

def index(request):
    timeline()
    script, div = components(
        {'MonthlySpend': bar_group(),
         'CumulativeSpend': line(),
         'ForecastFTE': bar_stack(),
         'Timeline': timeline(),
         }
    )
    context = dict(
        js_resource=INLINE.render_js(),
        css_resource=INLINE.render_css(),
        script=script,
        div=div,
    )
    return render(request, 'index.html', context)
