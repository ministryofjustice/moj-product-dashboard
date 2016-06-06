# -*- coding: utf-8 -*-
from model_mommy import mommy
import pytest

from dashboard.apps.prototype.models import Client, Project


@pytest.mark.django_db
def test_client():
    client = mommy.make(Client)
    projects = [mommy.make(Project, client=client) for _ in range(10)]
    assert str(client) == client.name
    sorted_names = sorted([p.name for p in projects])
    # can only compare by name as the id of the objects will be different
    assert [p.name for p in client.projects.order_by('name')] == sorted_names
