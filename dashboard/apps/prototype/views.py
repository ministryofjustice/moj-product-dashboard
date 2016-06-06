import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required

from .models import Project, Client


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


@login_required
def project_json(request):
    """
    send json for a project profilet
    """
    # TODO handle errors
    request_data = json.loads(request.body.decode())
    project = Project.objects.get(id=request_data['projectid'])
    return JsonResponse(project.profile())
