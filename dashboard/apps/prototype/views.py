import json

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotFound
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from dashboard.libs.date_tools import parse_date
from .models import Project, Client, ProjectGroup
from .tasks import sync_float


CUSTOMISED_GROUPS = 'Customised Groups'


@login_required
def project_html(request, id):
    if not id:
        id = Project.objects.visible().first().id
        return redirect(reverse(project_html, kwargs={'id': id}))
    try:
        Project.objects.visible().get(id=id)
    except (ValueError, Project.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project with id={}'.format(id))
    return render(request, 'portfolio.html')


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
        ProjectGroup.objects.get(id=id)
    except (ValueError, ProjectGroup.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find project group with id={}'.format(id))
    return render(request, 'portfolio.html')


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
    return JsonResponse(project_group.profile(freq='MS'))


@login_required
def service_html(request, id):
    if not id:
        id = Client.objects.filter(visible=True).first().id
        return redirect(reverse(service_html, kwargs={'id': id}))
    try:
        Client.objects.filter(visible=True).get(id=id)
    except (ValueError, Client.DoesNotExist):
        # TODO better error page
        return HttpResponseNotFound(
            'cannot find service with id={}'.format(id))
    return render(request, 'portfolio.html')


@login_required
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


@login_required
def portfolio_html(request):
    return render(request, 'portfolio.html')


@login_required
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
