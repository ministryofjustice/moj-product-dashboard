# -*- coding: utf-8 -*-
"""
unit tests views.py
"""
import json
import urllib
from unittest.mock import patch

from django.test import Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import pytest
from faker import Faker
from model_mommy import mommy
from rest_framework.test import APIRequestFactory

from dashboard.apps.dashboard.views import (
    product_html, product_json, service_html, service_json,
    product_group_html, product_group_json, DepartmentViewSet,
    sync_from_float)
from dashboard.apps.dashboard.models import (
    Area, Product, ProductGroup, Department, Person)


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
    product = mommy.make(Product)
    client = Client()
    rsp = client.get(reverse(product_html, kwargs={'id': product.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_product_html_without_productid():
    product = mommy.make(Product)
    client = make_login_client()
    rsp = client.get(reverse(product_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(product_html, kwargs={'id': product.id})


@pytest.mark.django_db
def test_product_html_with_valid_productid():
    client = make_login_client()
    product = mommy.make(Product)
    rsp = client.get(reverse(product_html, kwargs={'id': product.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_product_html_with_non_existing_id():
    client = make_login_client()
    product = mommy.make(Product)
    rsp = client.get(reverse(product_html, kwargs={'id': product.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_product_json_with_valid_id():
    client = make_login_client()
    product = mommy.make(Product)
    url = reverse(product_json, kwargs={'id': product.id})
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_product_json_with_invalid_id():
    client = make_login_client()
    url = '{}?{}'.format(reverse(product_json),
                         urllib.parse.urlencode({'id': 'invalid_id'}))
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_service_html_without_id():
    client = make_login_client()
    area = mommy.make(Area)
    rsp = client.get(reverse(service_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(service_html, kwargs={'id': area.id})


@pytest.mark.django_db
def test_service_html_with_valid_id():
    client = make_login_client()
    area = mommy.make(Area)
    rsp = client.get(reverse(service_html, kwargs={'id': area.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_service_html_with_non_existing_id():
    client = make_login_client()
    area = mommy.make(Area)
    rsp = client.get(reverse(service_html, kwargs={'id': area.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_service_json():
    client = make_login_client()
    area = mommy.make(Area)
    url = reverse(service_json, kwargs={'id': area.id})
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_service_json_with_invalid_id():
    client = make_login_client()
    url = '{}?{}'.format(reverse(service_json),
                         urllib.parse.urlencode({'id': 'invalid_id'}))
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_product_group_html_without_productid():
    group = mommy.make(ProductGroup)
    client = make_login_client()
    rsp = client.get(reverse(product_group_html))
    assert rsp.status_code == 302
    assert rsp.url == reverse(product_group_html, kwargs={'id': group.id})


@pytest.mark.django_db
def test_product_group_html_with_valid_productid():
    client = make_login_client()
    group = mommy.make(ProductGroup)
    rsp = client.get(reverse(product_group_html, kwargs={'id': group.id}))
    assert rsp.status_code == 200


@pytest.mark.django_db
def test_product_group_html_with_non_existing_id():
    client = make_login_client()
    group = mommy.make(ProductGroup)
    rsp = client.get(reverse(product_group_html, kwargs={'id': group.id + 1}))
    assert rsp.status_code == 404


@pytest.mark.django_db
def test_product_group_json_with_valid_id():
    client = make_login_client()
    group = mommy.make(ProductGroup)
    url = reverse(product_group_json, kwargs={'id': group.id})
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 200
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
def test_product_group_json_with_non_existing_id():
    client = make_login_client()
    url = reverse(product_group_json, kwargs={'id': 9999})
    rsp = client.get(url, content_type='application/json')
    assert rsp.status_code == 404
    assert rsp['Content-Type'] == 'application/json'


@pytest.mark.django_db
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
@patch('dashboard.apps.dashboard.views.sync_float.delay')
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


@pytest.mark.django_db
def test_department_list_view():
    departments = [mommy.make(Department) for _ in range(5)]

    view = DepartmentViewSet.as_view(actions={'get': 'list'})
    rsp = view(APIRequestFactory().get(''))
    assert rsp.status_code == 200
    results = rsp.data['results']
    assert {d['id'] for d in results} == {d.id for d in departments}
    assert 'persons' not in results[0]


@pytest.mark.django_db
def test_department_detail_view():
    departments = [mommy.make(Department) for _ in range(5)]
    persons = [mommy.make(Person, department=departments[0])
               for _ in range(2)]

    view = DepartmentViewSet.as_view(actions={'get': 'retrieve'})
    rsp = view(APIRequestFactory().get(''), pk=departments[0].pk)
    assert rsp.status_code == 200
    assert {p['id'] for p in rsp.data['persons']} == {p.id for p in persons}
