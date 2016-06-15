# -*- coding: utf-8 -*-
"""
unit tests views.py
"""
import json

from django.test import Client
from django.core.urlresolvers import reverse
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
import pytest
from faker import Faker
from model_mommy import mommy

from dashboard.apps.prototype.views import (
    index, project_html, project_json, area_html, area_json)
from dashboard.apps.prototype.models import Client as Area, Project


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


@pytest.mark.parametrize('view', [
    index,
    project_json
])
def test_login_required(view):
    client = Client()
    rsp = client.get(reverse(view))
    assert rsp.status_code == 302
    assert rsp.url.startswith(reverse(auth_views.login))


@pytest.mark.django_db
def test_index_no_projectid_no_data():
    client = make_login_client()
    rsp = client.get(reverse(index))
    assert rsp.status_code == 500


@pytest.mark.django_db
def test_index_no_projectid_with_data():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.get(reverse(index))
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
def test_area_html():
    client = make_login_client()
    area = mommy.make(Area)
    rsp = client.get(reverse(area_html, kwargs={'id': area.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_area_json():
    client = make_login_client()
    area = mommy.make(Area)
    rsp = client.post(
        reverse(area_json),
        json.dumps({'id': area.id}),
        content_type='application/json'
    )
    assert rsp.status_code == 200
