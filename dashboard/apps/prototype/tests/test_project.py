# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.libs.date_tools import parse_date, get_workdays
from dashboard.apps.prototype.models import (
    Project, Task, Person, Rate, Cost, RAG, Budget)
from prototype.constants import COST_TYPES, RAG_TYPES


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
    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=date.today()
    )
    assert project.first_task is None
    assert project.last_task is None

    assert project.people_costs(start_date=start_date, end_date=end_date) == 0
    profile = project.profile(freq='MS')
    assert 'name' in profile
    assert 'description' in profile
    assert len(profile['financial']) == 1
    assert next(iter(profile['financial'].values())) == {
        'additional': Decimal('0'),
        'budget': Decimal('0'),
        'contractor': Decimal('0'),
        'non-contractor': Decimal('0')
    }
    assert project.current_fte() == 0
    assert project.time_spent() == 0
    assert project.cost_to_date == 0
    assert project.total_cost == 0
    assert project.financial_rag == 'GREEN'


@pytest.mark.django_db
def test_project_profiles_without_frequency():
    profile = make_project().profile()
    financial = {
        'contractor': contractor_rate * man_days,
        'non-contractor': non_contractor_rate * man_days,
        'additional': Decimal('0'),
        'budget': Decimal('0')
    }
    key = '2016-01-01~2016-01-20'
    assert profile['financial'] == {key: financial}


@pytest.mark.django_db
def test_project_profiles_with_frequency():
    profile = make_project().profile(freq='W')  # weekly
    financial = {
        'contractor': contractor_rate * man_days,
        'non-contractor': non_contractor_rate * man_days,
        'additional': Decimal('0'),
        'budget': Decimal('0')
    }
    keys = [
        '2015-12-27~2016-01-02',
        '2016-01-03~2016-01-09',
        '2016-01-10~2016-01-16',
        '2016-01-17~2016-01-23',
    ]
    assert sorted(list(profile['financial'].keys())) == keys

    for key in ['contractor', 'non-contractor', 'additional']:
        expected = financial[key]
        assert sum(v[key] for v in profile['financial'].values()) == expected


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
        end_date=date(2018, 3, 31),
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
    mommy.make(
        Cost,
        project=project,
        start_date=date(2018, 4, 30),
        end_date=date(2018, 7, 31),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('100')
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

    assert project.additional_costs(
        start_date=date(2018, 4, 30),
        end_date=date(2018, 7, 31)) == Decimal('400')


@pytest.mark.django_db
def test_project_visible():
    mommy.make(Project, visible=False)
    mommy.make(Project, visible=True)

    assert Project.objects.visible().count() == 1


@pytest.mark.django_db
def test_project_time_spent_for_project_with_tasks():
    project = make_project()
    assert project.time_spent() == 8  # no start_date nor end_date
    assert project.time_spent(start_date=start_date) == 8  # no end_date
    assert project.time_spent(end_date=end_date) == 8  # no end_date
    assert project.time_spent(
        start_date=start_date,
        end_date=end_date) == 8  # with both start_date and end_date


@pytest.mark.django_db
def test_project_current_fte():
    project = make_project()
    assert project.current_fte() == 0  # no work has been done in the last week
    time_spent = project.time_spent()
    workdays = get_workdays(start_date, end_date)
    assert project.current_fte(start_date, end_date) == time_spent / workdays


@pytest.mark.django_db
def test_project_rag():
    project = make_project()
    assert project.rag() is None

    today = date.today()
    date_1 = today - timedelta(days=100)
    date_2 = today - timedelta(days=50)
    date_3 = today + timedelta(days=50)
    rag1 = mommy.make(
        RAG, project=project, rag=RAG_TYPES.GREEN, start_date=date_1)
    rag2 = mommy.make(
        RAG, project=project, rag=RAG_TYPES.AMBER, start_date=date_2)
    rag3 = mommy.make(
        RAG, project=project, rag=RAG_TYPES.RED, start_date=date_3)

    assert project.rag(on=date_1) == rag1
    assert project.rag(on=date_1 + timedelta(days=25)) == rag1
    assert project.rag(on=date_2) == rag2
    assert project.rag() == rag2
    assert project.rag(on=today) == rag2
    assert project.rag(on=today - timedelta(days=25)) == rag2
    assert project.rag(on=today + timedelta(days=25)) == rag2
    assert project.rag(on=today + timedelta(days=75)) == rag3


@pytest.mark.django_db
def test_project_budget():
    project = make_project()
    assert project.budget() == 0

    today = date.today()
    date_1 = today - timedelta(days=100)
    date_2 = today - timedelta(days=50)
    date_3 = today + timedelta(days=50)
    budget1 = mommy.make(
        Budget, project=project, budget=1000, start_date=date_1)
    budget2 = mommy.make(
        Budget, project=project, budget=1500, start_date=date_2)
    budget3 = mommy.make(
        Budget, project=project, budget=2000, start_date=date_3)

    assert project.budget(on=date_1) == budget1.budget
    assert project.budget(on=date_1 + timedelta(days=25)) == budget1.budget
    assert project.budget(on=date_2) == budget2.budget
    assert project.budget() == budget2.budget
    assert project.budget(on=today) == budget2.budget
    assert project.budget(on=today - timedelta(days=25)) == budget2.budget
    assert project.budget(on=today + timedelta(days=25)) == budget2.budget
    assert project.budget(on=today + timedelta(days=75)) == budget3.budget


@pytest.mark.django_db
def test_project_cost():
    project = make_project()
    cost = Decimal('50')
    mommy.make(
        Cost,
        project=project,
        start_date=start_date + timedelta(days=1),
        type=COST_TYPES.ONE_OFF,
        cost=cost
    )
    expected = (
        contractor_rate * man_days + non_contractor_rate * man_days + cost)
    assert project.cost_to_date == expected
    assert project.total_cost == expected

    # add a future task and cost. it shoudn't change
    # cost_to_date but total_cost
    contractor = mommy.make(Person, is_contractor=True)
    mommy.make(
        Rate,
        start_date=start_date,
        rate=contractor_rate,
        person=contractor
    )
    mommy.make(
        Task,
        person=contractor,
        project=project,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=3),
        days=2
    )
    mommy.make(
        Cost,
        project=project,
        start_date=date.today() + timedelta(days=100),
        type=COST_TYPES.ONE_OFF,
        cost=cost
    )
    assert project.cost_to_date == expected
    assert project.total_cost == expected + contractor_rate * 2 + cost


@pytest.mark.django_db
def test_project_first_date():
    project = make_project()

    first_task_start_date = parse_date(task_time_ranges[0][0])
    # without discover date,
    # first date is the start date of the first task
    assert project.first_date == first_task_start_date

    # with discover date before first task,
    # first date is the discovery date
    discovery_date = first_task_start_date - timedelta(days=1)
    project.discovery_date = discovery_date
    assert project.first_date == discovery_date

    # with discover date before first task,
    # first date is the start date of the first task
    discovery_date = first_task_start_date + timedelta(days=1)
    project.discovery_date = discovery_date
    assert project.first_date == first_task_start_date

    # without tasks,
    # first date is the discovery date
    project2 = mommy.make(Project)
    project2.discovery_date = date.today()
    assert project2.first_date == project2.discovery_date


@pytest.mark.django_db
def test_project_last_date():
    project = make_project()
    last_task_end_date = parse_date(task_time_ranges[-1][-1])

    # without project end date,
    # last date is the end date of the first task
    assert project.last_date == last_task_end_date

    # with project end date after end date of last task,
    # first date is the discovery date
    end_date = last_task_end_date + timedelta(days=1)
    project.end_date = end_date
    assert project.last_date == end_date

    # with project end date before end date of last task,
    # first date is the discovery date
    end_date = last_task_end_date - timedelta(days=1)
    project.end_date = end_date
    assert project.last_date == last_task_end_date

    # without tasks,
    # first date is the end date
    project2 = mommy.make(Project)
    project2.end_date = date.today()
    assert project2.last_date == project2.end_date


@pytest.mark.django_db
def test_project_phase():

    project = mommy.make(Project)
    assert project.phase == 'Not Defined'

    project.discovery_date = date.today() - timedelta(days=1)
    assert project.phase == 'Discovery'

    project.alpha_date = date.today() - timedelta(days=1)
    assert project.phase == 'Alpha'

    project.beta_date = date.today() - timedelta(days=1)
    assert project.phase == 'Beta'

    project.live_date = date.today() - timedelta(days=1)
    assert project.phase == 'Live'

    project.end_date = date.today() - timedelta(days=1)
    assert project.phase == 'Ended'


@pytest.mark.django_db
def test_default_start_date():
    project = make_project()

    first_task_start_date = parse_date(task_time_ranges[0][0])

    # without budget or cost, the first task start date
    # is the default start date.
    assert project.default_start_date == first_task_start_date

    # with a cost after the first task, the first task start date
    # is still the default start date.
    first_cost_start_date = first_task_start_date + timedelta(days=2)
    mommy.make(
        Cost,
        project=project,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert project.default_start_date == first_task_start_date

    # with a cost before the first task, the first cost start date
    # is the default start date.
    first_cost_start_date = first_task_start_date - timedelta(days=2)
    mommy.make(
        Cost,
        project=project,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert project.default_start_date == first_cost_start_date

    # with a budget allocated after the first cost, the first cost
    # start date is the default start date
    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=project.default_start_date + timedelta(days=2))
    assert project.default_start_date == first_cost_start_date

    # with a budget allocated before the first cost, the budget
    # start date is the default start date
    first_budget_start_date = project.default_start_date - timedelta(days=2)
    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=first_budget_start_date)
    assert project.default_start_date == first_budget_start_date


@pytest.mark.django_db
def test_default_end_date():
    project = make_project()

    last_task_end_date = parse_date(task_time_ranges[-1][-1])

    # without budget or cost, the last task end date
    # is the default start date.
    assert project.default_end_date == last_task_end_date

    # with a cost before the last task, the last task end date
    # is still the default start date.
    first_cost_start_date = last_task_end_date - timedelta(days=2)
    last_cost_start_date = last_task_end_date - timedelta(days=1)
    mommy.make(
        Cost,
        project=project,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        project=project,
        start_date=last_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert project.default_end_date == last_task_end_date

    # with a cost after the last task, the last cost start date
    # is the default end date.
    last_cost_start_date = last_task_end_date + timedelta(days=1)
    mommy.make(
        Cost,
        project=project,
        start_date=last_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert project.default_end_date == last_cost_start_date

    # with an end date for the last cost, the end date of the
    # last cost is the default end date.
    last_cost_end_date = last_cost_start_date + timedelta(days=2)
    mommy.make(
        Cost,
        project=project,
        start_date=last_cost_start_date - timedelta(days=1),
        end_date=last_cost_end_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert project.default_end_date == last_cost_end_date

    # with a budget allocated before the last cost, the cost
    # start date is the default end date
    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=last_cost_start_date - timedelta(days=2))
    assert project.default_end_date == last_cost_end_date

    # with a budget allocated after the last cost, the budget
    # start date is the default end date
    last_budget_start_date = project.default_end_date + timedelta(days=2)
    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=last_budget_start_date)
    assert project.default_end_date == last_budget_start_date


@pytest.mark.django_db
def test_default_end_date_no_dates():
    project = mommy.make(Project)
    with pytest.raises(ValueError):
        project.default_end_date


@pytest.mark.django_db
def test_project_financial_rag():
    project = mommy.make(Project)
    assert project.financial_rag == 'GREEN'

    mommy.make(
        Budget,
        project=project,
        budget=1000,
        start_date=date.today()
    )
    assert project.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        project=project,
        start_date=date.today() - timedelta(days=2),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('500')
    )
    assert project.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        project=project,
        start_date=date.today() + timedelta(days=2),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('500')
    )
    assert project.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        project=project,
        start_date=date.today() + timedelta(days=4),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('100')
    )
    assert project.financial_rag == 'AMBER'

    mommy.make(
        Cost,
        project=project,
        start_date=date.today() + timedelta(days=5),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('1')
    )
    assert project.financial_rag == 'RED'


@pytest.mark.django_db
def test_admin_url():
    project = make_project()
    expected = '/admin/prototype/project/{}/change/'.format(project.id)
    assert project.admin_url == expected
