from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.apps.prototype.models import ProjectGroup, Client
from .test_project import make_project


@pytest.mark.django_db
def test_project_group():
    p1 = make_project()
    p2 = make_project()
    pg = ProjectGroup(name='PG1')
    pg.save()
    assert str(pg) == 'PG1'

    pg.projects.add(p1)
    pg.projects.add(p2)
    profile = pg.profile()
    financial = {
        '2016-01-01~2016-01-31': {
            'non-contractor': Decimal('2800.0000000'),
            'contractor': Decimal('3200.0000000'),
            'budget': Decimal('0'),
            'additional': Decimal('0')
        }
    }
    assert profile['financial'] == financial
    assert profile['name'] == 'PG1'


@pytest.mark.django_db
def test_merge_financial():
    financial1 = {
        '2016-01-01~2016-01-31': {
            'contractor': 1600,
            'non-contractor': 1400,
            'additional': 1000,
            'budget': 5000
        }
    }
    assert ProjectGroup.merge_financial(financial1, {}) == financial1
    financial2 = {
        '2016-01-01~2016-01-31': {
            'contractor': 1600,
            'non-contractor': 1400,
            'additional': 500,
            'budget': 4000,
        }
    }
    expected = {
        '2016-01-01~2016-01-31': {
            'contractor': 3200,
            'non-contractor': 2800,
            'additional': 1500,
            'budget': 9000
        }
    }
    assert ProjectGroup.merge_financial(financial1, financial2) == expected

    financial2 = {
        '2016-02-01~2016-02-28': {
            'contractor': 1600,
            'non-contractor': 1400,
            'additional': 500,
            'budget': 4000,
        }
    }
    expected = {
        '2016-01-01~2016-01-31': {
            'contractor': 1600,
            'non-contractor': 1400,
            'additional': 1000,
            'budget': 5000
        },
        '2016-02-01~2016-02-28': {
            'contractor': 1600,
            'non-contractor': 1400,
            'additional': 500,
            'budget': 4000,
        }
    }
    assert ProjectGroup.merge_financial(financial1, financial2) == expected


@pytest.mark.django_db
def test_project_group_client():
    client1 = mommy.make(Client, name='client1')

    p1 = make_project()
    p2 = make_project()
    p1.client = client1
    p2.client = client1
    p1.save()
    p2.save()

    pg = ProjectGroup(name='PG1')
    pg.save()
    pg.projects.add(p1)
    pg.projects.add(p2)

    assert pg.client == client1

    client2 = mommy.make(Client, name='client2')
    p2.client = client2
    p2.save()
    assert pg.client is None
