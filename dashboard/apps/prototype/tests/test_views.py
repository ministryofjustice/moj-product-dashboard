# -*- coding: utf-8 -*-
"""
unit tests views.py
"""
import json
from unittest.mock import patch

from django.test import Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import pytest
from faker import Faker
from model_mommy import mommy

from dashboard.apps.prototype.views import (
    project_html, project_json, service_html, service_json,
    project_group_html, project_group_json, sync_from_float)
from dashboard.apps.prototype.models import (
    Client as Service, Project, ProjectGroup)


def make_login_client():
    fake = Faker()
    password = fake.password()
    user = User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password=password
    )
    client = Client()
    assert client.login(
        username=user.username,
        password=password  # user.password is hashed
    ), 'login failed!'
    return client


@pytest.mark.django_db
def test_login_not_required():
    project = mommy.make(Project)
    client = Client()
    rsp = client.get(reverse(project_html, kwargs={'id': project.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_project_html_without_projectid():
    project = mommy.make(Project)
    client = make_login_client()
    rsp = client.get(reverse(project_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(project_html, kwargs={'id': project.id})


@pytest.mark.django_db
def test_project_html_with_valid_projectid():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.get(reverse(project_html, kwargs={'id': project.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_project_html_with_non_existing_id():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.get(reverse(project_html, kwargs={'id': project.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_project_json_with_valid_id():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.post(
        reverse(project_json),
        json.dumps({'id': project.id}),
        content_type='application/json'
    )
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_project_json_with_invalid_id():
    client = make_login_client()
    rsp = client.post(
        reverse(project_json),
        json.dumps({'id': 'invalid_id'}),
        content_type='application/json'
    )
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_service_html_without_id():
    client = make_login_client()
    service = mommy.make(Service)
    rsp = client.get(reverse(service_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(service_html, kwargs={'id': service.id})


@pytest.mark.django_db
def test_service_html_with_valid_id():
    client = make_login_client()
    service = mommy.make(Service)
    rsp = client.get(reverse(service_html, kwargs={'id': service.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_service_html_with_non_existing_id():
    client = make_login_client()
    service = mommy.make(Service)
    rsp = client.get(reverse(service_html, kwargs={'id': service.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_service_json():
    client = make_login_client()
    service = mommy.make(Service)
    rsp = client.post(
        reverse(service_json),
        json.dumps({'id': service.id}),
        content_type='application/json'
    )
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_service_json_with_invalid_id():
    client = make_login_client()
    rsp = client.post(
        reverse(service_json),
        json.dumps({'id': 'invalid_id'}),
        content_type='application/json'
    )
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_project_group_html_without_projectid():
    group = mommy.make(ProjectGroup)
    client = make_login_client()
    rsp = client.get(reverse(project_group_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(project_group_html, kwargs={'id': group.id})


@pytest.mark.django_db
def test_project_group_html_with_valid_projectid():
    client = make_login_client()
    group = mommy.make(ProjectGroup)
    rsp = client.get(reverse(project_group_html, kwargs={'id': group.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_project_group_html_with_non_existing_id():
    client = make_login_client()
    group = mommy.make(ProjectGroup)
    rsp = client.get(reverse(project_group_html, kwargs={'id': group.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_project_group_json_with_valid_id():
    client = make_login_client()
    group = mommy.make(ProjectGroup)
    rsp = client.post(
        reverse(project_group_json),
        json.dumps({'id': group.id}),
        content_type='application/json'
    )
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_project_group_json_with_invalid_id():
    client = make_login_client()
    rsp = client.post(
        reverse(project_group_json),
        json.dumps({'id': 'invalid_id'}),
        content_type='application/json'
    )
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
@patch('dashboard.apps.prototype.views.sync_float.delay')
def test_sync_float(mock_sync_float):
    client = make_login_client()
    rsp = client.post(
        reverse(sync_from_float),
        json.dumps({}),
        content_type='application/json'
    )
    mock_sync_float.assert_called_once_with()
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'
    assert rsp.json() == {'status': 'STARTED'}
