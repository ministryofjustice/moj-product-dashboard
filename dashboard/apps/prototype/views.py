import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

from .models import Project, Client
from dashboard.libs.figure_gen import get_figure


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


@login_required
def index(request):
    try:
        project_id = request.GET['projectid']
    except KeyError:
        project_id = Project.objects.first().id
        return redirect('/?projectid={}'.format(project_id))
    try:
        project_id = int(project_id)
        project = Project.objects.get(id=project_id)
    except (ValueError, Project.DoesNotExist):
        # TODO better error page
        return HttpResponseBadRequest(
            'invalid projectid "{}"'.format(project_id))
    areas = {
        area.name: {p.id: p.name for p in area.projects.all()}
        for area in Client.objects.all()
    }
    areas = OrderedDict(sorted([(k, v) for k, v in areas.items() if v]))
    context = {'areas': areas,  'project': project}
    return render(request, 'index.html', context)


def send_figure(request):

    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = json.loads(request.body.decode())
    else:
        return HttpResponseBadRequest()

    print(request_data)

    figure = get_figure(request_data['requested_figure'], request_data)

    return JsonResponse(figure, safe=False)
