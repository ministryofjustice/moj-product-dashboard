# -*- coding: utf-8 -*-
from model_mommy import mommy
import pytest

from dashboard.apps.prototype.models import Client, Project


@pytest.mark.django_db
def test_client():
    client = mommy.make(Client)
    projects = [mommy.make(Project, client=client) for _ in range(10)]
    assert str(client) == client.name
    sorted_pids = sorted([p.id for p in projects])
    assert [p.id for p in client.projects.order_by('id')] == sorted_pids


@pytest.mark.django_db
def test_client_profile():
    client = mommy.make(Client)
    projects = [mommy.make(Project, client=client) for _ in range(10)]
    profile1 = client.profile()
    profile2 = client.profile(project_ids=[p.id for p in projects])
    assert profile1 == profile2
