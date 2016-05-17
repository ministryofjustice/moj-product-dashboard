# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from collections import OrderedDict

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.charts import Bar, Line
from bokeh.charts.attributes import CatAttr
from bokeh.models import (
    PrintfTickFormatter, NumeralTickFormatter, DatetimeTickFormatter)

from dashboard.libs import data_generator


STYLE = {
    'plot_width': 400,
    'plot_height': 200,
    'responsive': True,
    'logo': None,
    'xlabel': '',
    'ylabel': '',
    'toolbar_location': 'above',
}

PROJECT_PHASES = OrderedDict([
    ('discovery', {'color': 'olive'}),
    ('alpha', {'color': 'navy'}),
    ('beta', {'color': 'red'}),
    ('live', {'color': 'green'}),
    ('project end', {'color': 'blue'})
])


def monthly_spendings(spendings):
    months = []
    keys = []
    values = []
    for month, props in spendings.items():
        month_str = month.strftime('%b %y')
        for key, val in props.items():
            months.append(month_str)
            keys.append(key)
            values.append(val)

    data = {
        'months': months,
        'keys': keys,
        'values': values
    }
    label = CatAttr(columns='months', sort=False)
    bar = Bar(data, values='values', label=label, group='keys',
              color=['dodgerblue', 'lightblue'],
              agg='median', title="Monthly Spend",
              legend='top_right', **STYLE)
    # TODO this does not feel right, but bokeh doesn't present
    # a better way to do it.
    bar._yaxis.formatter = PrintfTickFormatter(format='£%dk')
    return bar


def line():
    xyvalues = np.array([[2, 7, 15, 20, 26], ])

    line = Line(xyvalues, title="Cumulative Spend", legend="top_left",
                **STYLE)
    return line


def forecast_stack(forecast):
    months = []
    keys = []
    values = []
    for month, props in forecast.items():
        month_str = month.strftime('%b %y')
        for key, val in props.items():
            months.append(month_str)
            keys.append(key)
            values.append(val)
    data = {
        'months': months,
        'keys': keys,
        'values': values
    }
    label = CatAttr(columns='months', sort=False)
    bar = Bar(data, values='values', label=label, stack='keys',
              color=['dodgerblue', 'lightblue'],
              title="Forecast FTE Civil Servant/Contractor split",
              legend='top_right', **STYLE)
    # TODO this does not feel right, but bokeh doesn't present
    # a better way to do it.
    bar._yaxis.formatter = NumeralTickFormatter(format='0.00')
    return bar


def project_timeline(timeline):
    padding = timedelta(days=60)
    start_date = timeline[list(PROJECT_PHASES.keys())[0]]['date']
    end_date = max(timeline[list(PROJECT_PHASES.keys())[-1]]['date'],
                   datetime.now())

    x = [datetime(year=period.year, month=period.month, day=1) for period in
         pd.period_range((start_date - padding).strftime('%Y-%m-%d'),
                         (end_date + padding).strftime('%Y-%m-%d'),
                         freq='M')
         ]
    p = figure(title='Timeline', plot_width=400,
               plot_height=120, responsive=True,
               x_axis_type="datetime", y_range=(-2, 8), logo=None)
    p.line(x=x, y=[0] * len(x))
    p.yaxis.visible = None
    p.ygrid.grid_line_color = None
    p.outline_line_color = None
    p.xaxis.formatter = DatetimeTickFormatter(formats=dict(
        days=["%b %y"],
        months=["%b %y"],
        years=["%b %y"],
    ))

    for phase, props in PROJECT_PHASES.items():
        date = timeline[phase]['date']
        p.diamond([date], [0], size=10, color=props['color'],
                  alpha=0.5, legend=phase)

    p.circle([datetime.now()], [0], size=10,
             color="black", alpha=0.5, legend="today")
    p.legend.orientation = 'top_left'
    p.legend.background_fill_alpha = 0.5
    return p


@login_required
def index(request):
    script, div = components({
        'MonthlySpend': monthly_spendings(
            data_generator.gen_monthly_spendings()),
        'CumulativeSpend': line(),
        'ForecastFTE': forecast_stack(data_generator.gen_forcast()),
        'Timeline': project_timeline(data_generator.gen_project_timeline()),
    })
    today = datetime.now().strftime('%d %b %Y')
    context = dict(
        js_resource=INLINE.render_js(),
        css_resource=INLINE.render_css(),
        script=script,
        div=div,
        today=today,
    )
    return render(request, 'index_bokeh.html', context)


