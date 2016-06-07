# -*- coding: utf-8 -*-
from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.apps.prototype.models import Project, Task, Person, Rate
from dashboard.libs.date_tools import parse_date


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

    assert project.money_spent(start_date=start_date, end_date=end_date) == 0
    profile = project.profile(freq='MS')
    assert 'name' in profile
    assert 'description' in profile
    assert profile['spendings'] == {}


@pytest.mark.django_db
def test_project_profiles():
    profile = make_project().profile()
    spendings = {'contractor': contractor_rate * man_days,
                 'non-contractor': non_contractor_rate * man_days}
    assert profile['spendings'] == {'2016-01': spendings}


@pytest.mark.django_db
def test_project_money_spent():
    project = make_project()
    assert project.money_spent(
        start_date=start_date,
        end_date=end_date,
        contractor_only=True) == contractor_rate * man_days
    assert project.money_spent(
        start_date=start_date,
        end_date=end_date,
        non_contractor_only=True) == non_contractor_rate * man_days

    with pytest.raises(ValueError):
        project.money_spent(
            start_date=start_date,
            end_date=end_date,
            non_contractor_only=True,
            contractor_only=True
        )
