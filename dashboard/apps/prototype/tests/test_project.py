# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.libs.date_tools import parse_date
from dashboard.apps.prototype.models import Project, Task, Person, Rate, Cost
from prototype.constants import COST_TYPES


task_time_ranges = [
    ('2016-01-01', '2016-01-06'),  # 1st finishes later than 2nd
    ('2016-01-03', '2016-01-05'),
    ('2016-01-14', '2016-01-15'),
    ('2016-01-10', '2016-01-20'),  # last starts earlier than the one prior
]
start_date = parse_date(task_time_ranges[0][0])
end_date = parse_date(task_time_ranges[-1][1])
contractor_rate = Decimal('400')
non_contractor_rate = Decimal('350')
man_days = len(task_time_ranges)  # 1 day on each task


def make_project():
    project = mommy.make(Project)
    contractor = mommy.make(Person, is_contractor=True)
    non_contractor = mommy.make(Person, is_contractor=False)
    mommy.make(
        Rate,
        start_date=start_date,
        rate=contractor_rate,
        person=contractor
    )
    mommy.make(
        Rate,
        start_date=start_date,
        rate=non_contractor_rate,
        person=non_contractor
    )
    for sd, ed in task_time_ranges:
        mommy.make(
            Task,
            person=contractor,
            project=project,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
        mommy.make(
            Task,
            person=non_contractor,
            project=project,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
    return project


@pytest.mark.django_db
def test_project_first_last_task_dates():
    project = make_project()
    assert project.first_task.start_date == start_date
    assert project.last_task.end_date == end_date


@pytest.mark.django_db
def test_project_without_tasks():
    project = mommy.make(Project)
    assert project.first_task is None
    assert project.last_task is None

    assert project.people_costs(start_date=start_date, end_date=end_date) == 0
    profile = project.profile(freq='MS')
    assert 'name' in profile
    assert 'description' in profile
    assert profile['financial'] == {}


@pytest.mark.django_db
def test_project_profiles():
    profile = make_project().profile()
    financial = {'contractor': contractor_rate * man_days,
                 'non-contractor': non_contractor_rate * man_days,
                 'additional': Decimal('0'),
                 'budget': Decimal('0')}
    assert profile['financial'] == {'2016-01': financial}


@pytest.mark.django_db
def test_project_people_costs():
    project = make_project()
    assert project.people_costs(
        start_date=start_date,
        end_date=end_date,
        contractor_only=True) == contractor_rate * man_days
    assert project.people_costs(
        start_date=start_date,
        end_date=end_date,
        non_contractor_only=True) == non_contractor_rate * man_days

    with pytest.raises(ValueError):
        project.people_costs(
            start_date=start_date,
            end_date=end_date,
            non_contractor_only=True,
            contractor_only=True
        )


@pytest.mark.django_db
def test_project_costs():
    project = mommy.make(Project)
    mommy.make(
        Cost,
        project=project,
        start_date=date(2015, 1, 1),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        project=project,
        start_date=date(2016, 1, 1),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        project=project,
        start_date=date(2016, 1, 31),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('55')
    )
    mommy.make(
        Cost,
        project=project,
        start_date=date(2016, 1, 3),
        type=COST_TYPES.ANNUALLY,
        cost=Decimal('60')
    )

    assert project.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2016, 1, 2)) == Decimal('50')

    assert project.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2016, 1, 3)) == Decimal('110')

    assert project.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2017, 2, 3)) == Decimal('885')
