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

from dashboard.apps.prototype.views import index, project_json
from dashboard.apps.prototype.models import Project


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
    assert rsp.url == reverse(index) + '?projectid={}'.format(project.id)


@pytest.mark.django_db
def test_index_with_valid_projectid():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.get(reverse(index), {'projectid': project.id})
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_index_with_invalid_projectid():
    client = make_login_client()
    mommy.make(Project)
    rsp = client.get(reverse(index), {'projectid': 'invalid_id'})
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_project_json_with_valid_projectid():
    client = make_login_client()
    project = mommy.make(Project)
    rsp = client.post(
        reverse(project_json),
        json.dumps({'projectid': project.id}),
        content_type='application/json'
    )
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_project_json_with_invalid_projectid():
    client = make_login_client()
    rsp = client.post(
        reverse(project_json),
        json.dumps({'projectid': 'invalid_id'}),
        content_type='application/json'
    )
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'
