import datetime
import json
from dateutil import relativedelta
import random
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest

from .models import Person, Project, Client, Task, Rate
from django.views.decorators.csrf import csrf_exempt


def get_total_times(projects):

    project_days = []
    project_names = []

    for project in projects:
        tasks = project.tasks.all()

        total_days = 0
        for task in tasks:
            total_days += task.days

        project_days.append(total_days)
        project_names.append(project.name)

    return project_names, project_days


def index(request):

    return render(request, 'index.html')


def simple(request):

    return render(request, 'simple.html')


def comparison(request):

    projects = Project.objects.all()

    project_names, project_days = get_total_times(projects)

    layout = {}

    trace = {
        'x': project_names,
        'y': project_days,
        'type': 'bar',
    }

    response = {
        'data': [trace],
        'layout': layout,
    }

    return JsonResponse(response, safe=False)


def get_x_axis(date):

    x_axis = []

    x_axis.append(date.strftime('%B %Y'))

    for i in range(1, 11):
        date += relativedelta.relativedelta(months=1)
        x_axis.append(date.strftime('%B %Y'))

    return x_axis


def send_figure(request):

    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = json.loads(request.body.decode())
    else:
        return HttpResponseBadRequest()

    print(request_data)



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

        'showlegend': False,

        'margin': {
            'l': 50,
            'r': 100,
            'b': 100,
            't': 100,
            'pad': 4
        },

    }

    response = {
        'data': [trace],
        'layout': layout,
    }

    return JsonResponse(response, safe=False)
