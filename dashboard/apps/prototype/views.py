import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import (JsonResponse, HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.contrib.auth.decorators import login_required

from .models import Person, Project, Client, Task, Rate
from dashboard.libs.figure_gen import get_data



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
        return HttpResponseNotFound(
            'cannot find project with projectid={}'.format(project_id))
    areas = {
        area.name: {p.id: p.name for p in area.projects.all()}
        for area in Client.objects.all()
    }
    areas = OrderedDict(sorted([(k, v) for k, v in areas.items() if v]))
    context = {'areas': areas,  'project': project}
    return render(request, 'index.html', context)


def send_data(request):

    if request.method == 'GET':
        request_data = request.GET
    elif request.method == 'POST':
        request_data = json.loads(request.body.decode())
    else:
        return HttpResponseBadRequest()

    data = get_data(request_data)

    return JsonResponse(data, safe=False)
