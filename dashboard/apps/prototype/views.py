import json

from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from dashboard.libs.date_tools import parse_date
from .models import Project, Client, ProjectGroup
from .tasks import sync_float


def _project_meta(request, project):
    meta = {
        'can_edit': project.can_user_change(request.user),
        'admin_url': request.build_absolute_uri(project.admin_url)
    }
    return meta


def project_html(request, id):
    if not id:
        id = Project.objects.visible().first().id
        return redirect(reverse(project_html, kwargs={'id': id}))
    try:
        Project.objects.visible().get(id=id)
    except (ValueError, Project.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


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
    profile = project.profile(
        start_date=start_date,
        end_date=end_date,
        freq='MS')
    meta = _project_meta(request, project)
    # use __meta__ to avoid potential key conflict
    # if meta grows bigger, put meta and profile in
    # different name spaces.
    return JsonResponse({**profile, '__meta__': meta})


def project_group_html(request, id):
    if not id:
        id = ProjectGroup.objects.first().id
        return redirect(reverse(project_group_html, kwargs={'id': id}))
    try:
        ProjectGroup.objects.get(id=id)
    except (ValueError, ProjectGroup.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


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
    profile = project_group.profile(freq='MS')
    meta = _project_meta(request, project_group)
    # use __meta__ to avoid potential key conflict
    # if meta grows bigger, put meta and profile in
    # different name spaces.
    return JsonResponse({**profile, '__meta__': meta})


def service_html(request, id):
    if not id:
        id = Client.objects.filter(visible=True).first().id
        return redirect(reverse(service_html, kwargs={'id': id}))
    try:
        Client.objects.filter(visible=True).get(id=id)
    except (ValueError, Client.DoesNotExist):
        raise Http404
    return render(request, 'common.html')


def service_json(request):
    request_data = json.loads(request.body.decode())
    try:
        client = Client.objects.filter(visible=True).get(id=request_data['id'])
    except (ValueError, Client.DoesNotExist):
        error = 'cannot find service area with id={}'.format(
            request_data['id'])
        return JsonResponse({'error': error}, status=404)
    # get the profile of the service
    return JsonResponse(client.profile())


def portfolio_html(request):
    return render(request, 'common.html', {'body_classes': 'portfolio'})


def portfolio_json(request):
    result = {client.id: client.profile() for client
              in Client.objects.filter(visible=True)}
    return JsonResponse(result)


@login_required
@require_http_methods(['POST'])
def sync_from_float(request):
    sync_float.delay()
    return JsonResponse({
        'status': 'STARTED'
    })
