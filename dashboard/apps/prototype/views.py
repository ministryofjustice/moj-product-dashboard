import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import (
    JsonResponse, HttpResponseNotFound, HttpResponseServerError)
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

from .models import Project, Client


@login_required
def index(request):
    # index page redirect /?projectid=:id to /projects/:id
    # when no 'projectid' is provided, pick the first
    try:
        project_id = request.GET['projectid']
    except KeyError:
        try:
            project_id = Project.objects.visible().first().id
        except AttributeError:  # when no project objects in the db
            # TODO better error page
            return HttpResponseServerError('cannot find any project')
    return redirect(reverse(project_html, kwargs={'id': project_id}))


@login_required
def project_html(request, id):
    try:
        project = Project.objects.visible().get(id=id)
    except (ValueError, Project.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project with id={}'.format(id))
    areas = {
        area.name: {p.id: p.name for p in area.projects.visible()}
        for area in Client.objects.all()
    }
    areas = OrderedDict(sorted([(k, v) for k, v in areas.items() if v]))
    context = {'areas': areas,  'project': project}
    return render(request, 'project.html', context)


@login_required
def project_json(request):
    """
    send json for a project profilet
    """
    # TODO handle errors
    request_data = json.loads(request.body.decode())
    try:
        project = Project.objects.visible().get(
            id=request_data['id'])
    except (ValueError, Project.DoesNotExist):
        error = 'cannot find project with id={}'.format(request_data['id'])
        return JsonResponse({'error': error}, status=404)
    return JsonResponse(project.profile())


@login_required
def area_html(request, id):
    areas = {c.id: c.name for c in Client.objects.all()}
    context = {'areas': areas, 'id': int(id)}
    return render(request, 'area.html', context=context)


@login_required
def area_json(request):
    return JsonResponse({'data': 'area_json'})
