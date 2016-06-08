import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import (
    JsonResponse, HttpResponseNotFound, HttpResponseServerError)
from django.contrib.auth.decorators import login_required

from .models import Project, Client


@login_required
def index(request):
    # when no 'projectid' is provided redirect to the first project
    try:
        project_id = request.GET['projectid']
    except KeyError:
        try:
            project_id = Project.objects.visible().first().id
            return redirect('/?projectid={}'.format(project_id))
        except AttributeError:  # when no project objects in the db
            # TODO better error page
            return HttpResponseServerError('cannot find any project')

    try:
        project = Project.objects.visible().get(id=project_id)
    except (ValueError, Project.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project with projectid={}'.format(project_id))
    areas = {
        area.name: {p.id: p.name for p in area.projects.visible()}
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
    try:
        project = Project.objects.visible().get(
            id=request_data['projectid'])
    except (ValueError, Project.DoesNotExist):
        error = 'cannot find project with projectid={}'.format(
            request_data['projectid'])
        return JsonResponse({'error': error}, status=404)
    return JsonResponse(project.profile())
