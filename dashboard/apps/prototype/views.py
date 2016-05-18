import datetime
from dateutil import relativedelta
import random
from django.shortcuts import render
from django.http import JsonResponse


def get_x_axis(date):

    x_axis = []

    x_axis.append(date.strftime('%B %Y'))

    for i in range(1, 11):
        date += relativedelta.relativedelta(months=1)
        x_axis.append(date.strftime('%B %Y'))

    return x_axis


def index(request):

    return render(request, 'index.html')


def data_response(request):

    date = datetime.datetime(2016, 1, 1, 12, 0, 0)

    x_axis = get_x_axis(date)

    y_axis = []

    for month in x_axis:

        y_axis.append(random.random() * 100)

    trace = {
        'x': x_axis,
        'y': y_axis,
        'type': 'bar',
    }

    layout = {
        # 'height': 350,
        # 'width': 350,
        'showlegend': False,

        'margin': {
            'l': 50,
            'r': 100,
            'b': 100,
            't': 100,
            'pad': 4
        },

        # 'paper_bgcolor': '#7f7f7f',
        # 'plot_bgcolor': '#c7c7c7',
    }

    response = {
        'data': [trace],
        'layout': layout,
    }

    # response = trace

    return JsonResponse(response, safe=False)
