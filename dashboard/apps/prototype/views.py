import json
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.http import (
    JsonResponse, HttpResponseNotFound, HttpResponseServerError)
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from dashboard.libs.date_tools import parse_date
from .models import Project, Client, ProjectGroup
from .tasks import sync_float


CUSTOMISED_GROUPS = 'Customised Groups'


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
    if not id:
        id = Project.objects.visible().first().id
        return redirect(reverse(project_html, kwargs={'id': id}))
    try:
        project = Project.objects.visible().get(id=id)
    except (ValueError, Project.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project with id={}'.format(id))
    services = {
        service.name: {p.id: p.name for p in service.projects.visible()}
        for service in Client.objects.all()
    }
    services = OrderedDict(sorted([(k, v) for k, v in services.items() if v]))
    context = {
        'selected_id': project.id,
        'project_type': 'project',
        'service_to_projects': combine_project_and_project_group()
    }
    return render(request, 'project.html', context)


@login_required
def project_json(request):
    """
    send json for a project profilet
    """
    # TODO handle errors
    request_data = json.loads(request.body.decode())
    try:
        project = Project.objects.visible().get(id=request_data['id'])
    except (ValueError, Project.DoesNotExist):
        error = 'cannot find project with id={}'.format(request_data['id'])
        return JsonResponse({'error': error}, status=404)

    start_date = request_data.get('startDate')
    if start_date:
        start_date = parse_date(start_date)
    end_date = request_data.get('endDate')
    if end_date:
        end_date = parse_date(end_date)
    # get the profile of the project for each month
    return JsonResponse(project.profile(
        start_date=start_date,
        end_date=end_date,
        freq='MS'))


@login_required
def project_group_html(request, id):
    if not id:
        id = ProjectGroup.objects.first().id
        return redirect(reverse(project_group_html, kwargs={'id': id}))
    try:
        project_group = ProjectGroup.objects.get(id=id)
    except (ValueError, ProjectGroup.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project group with id={}'.format(id))
    context = {
        'selected_id': project_group.id,
        'project_type': 'project_group',
        'service_to_projects': combine_project_and_project_group()
    }
    return render(request, 'project_group.html', context)


def combine_project_and_project_group():
    """
    combine project and project group and then group by client
    """
    project_ids_in_a_group = [
        p.id
        for pg in ProjectGroup.objects.all()
        for p in pg.projects.all()
    ]
    service_to_projects = {
        service.name: {
            p.id: {
                'id': p.id,
                'name': p.name,
                'url': reverse(project_html, kwargs={'id': p.id}),
                'type': 'project'
            }
            for p in service.projects.visible()
            if p.id not in project_ids_in_a_group
        }
        for service in Client.objects.all()
    }
    for project_group in ProjectGroup.objects.all():
        service = project_group.client
        service_name = service.name if service else CUSTOMISED_GROUPS
        service_dict = service_to_projects.setdefault(service_name, {})
        service_dict[project_group.id] = {
            'id': project_group.id,
            'name': project_group.name,
            'url': reverse(
                project_group_html, kwargs={'id': project_group.id}),
            'type': 'project_group'
        }

    def sort_project_by_name(id_to_project):
        return OrderedDict(
            sorted(id_to_project.items(), key=lambda p: p[1]['name']))

    service_to_projects = OrderedDict(
        sorted([
            (k, sort_project_by_name(v)) for k, v in
            service_to_projects.items() if v
        ]))
    try:
        service_to_projects.move_to_end(CUSTOMISED_GROUPS)
    except KeyError:
        pass
    return service_to_projects


@login_required
def project_group_json(request):
    """
    send json for a project group profilet
    """
    # TODO handle errors
    request_data = json.loads(request.body.decode())
    try:
        project_group = ProjectGroup.objects.get(id=request_data['id'])
    except (ValueError, ProjectGroup.DoesNotExist):
        error = 'cannot find project group with id={}'.format(
            request_data['id'])
        return JsonResponse({'error': error}, status=404)

    # get the profile of the project group for each month
    return JsonResponse(project_group.profile())


@login_required
def service_html(request, id):
    if not id:
        id = Client.objects.first().id
        return redirect(reverse(service_html, kwargs={'id': id}))
    try:
        service = Client.objects.get(id=id)
    except (ValueError, Client.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find service with id={}'.format(id))
    services = {c.id: c.name for c in Client.objects.all()}
    context = {'services': services, 'service': service}
    return render(request, 'service.html', context=context)


@login_required
def service_json(request):
    request_data = json.loads(request.body.decode())
    try:
        client = Client.objects.get(id=request_data['id'])
    except (ValueError, Client.DoesNotExist):
        error = 'cannot find service area with id={}'.format(
            request_data['id'])
        return JsonResponse({'error': error}, status=404)
    # get the profile of the service
    return JsonResponse(client.profile())


@login_required
def portfolio_html(request):
    return render(request, 'portfolio.html')


@login_required
@cache_page(60 * 15)
def portfolio_json(request):
    result = {client.id: client.profile() for client in Client.objects.all()}
    return JsonResponse(result)


@login_required
def sync_from_float(request):
    sync_float.delay()
    return JsonResponse({
        'status': 'STARTED'
    })
