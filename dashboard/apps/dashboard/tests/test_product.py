# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.libs.date_tools import parse_date, get_workdays
from dashboard.apps.dashboard.models import (
    Product, Area, Task, Person, Rate, Cost, ProductStatus, Budget,
    PersonCost)
from dashboard.apps.dashboard.constants import COST_TYPES, STATUS_TYPES


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


def make_product():
    product = mommy.make(Product)
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
            product=product,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
        mommy.make(
            Task,
            person=non_contractor,
            product=product,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
    return product


@pytest.mark.django_db
def test_product_first_last_task_dates():
    product = make_product()
    assert product.first_task.start_date == start_date
    assert product.last_task.end_date == end_date


@pytest.mark.django_db
def test_product_without_tasks():
    product = mommy.make(Product)
    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=date.today()
    )
    assert product.first_task is None
    assert product.last_task is None

    assert product.people_costs(start_date=start_date, end_date=end_date) == 0
    profile = product.profile(
        start_date=start_date, end_date=end_date, freq='MS')
    assert 'name' in profile
    assert 'description' in profile
    assert len(profile['financial']['time_frames']) == 1
    assert next(iter(profile['financial']['time_frames'].values())) == {
        'additional': Decimal('0'),
        'budget': Decimal('0'),
        'contractor': Decimal('0'),
        'non-contractor': Decimal('0'),
        'savings': Decimal('0'),
        'remaining': Decimal('0'),
        'total': Decimal('0')
    }
    assert product.time_spent() == 0
    assert product.current_fte() == 0
    assert product.cost_to_date == 0
    assert product.total_cost == 0
    assert product.financial_rag == 'GREEN'


@pytest.mark.django_db
def test_product_profiles_without_frequency():
    profile = make_product().profile(freq=None)
    contractor = contractor_rate * man_days
    non_contractor = non_contractor_rate * man_days
    financial = {
        'contractor': contractor,
        'non-contractor': non_contractor,
        'additional': Decimal('0'),
        'budget': Decimal('0'),
        'savings': Decimal('0'),
        'total': contractor + non_contractor,
        'remaining': Decimal('0') - contractor - non_contractor
    }
    key = '2016-01-01~2016-01-20'
    assert profile['financial']['time_frames'] == {key: financial}


@pytest.mark.django_db
def test_product_profiles_with_frequency():
    profile = make_product().profile(freq='W')  # weekly
    financial = {
        'contractor': contractor_rate * man_days,
        'non-contractor': non_contractor_rate * man_days,
        'additional': Decimal('0'),
        'budget': Decimal('0'),
        'savings': Decimal('0')
    }
    keys = [
        '2015-12-27~2016-01-02',
        '2016-01-03~2016-01-09',
        '2016-01-10~2016-01-16',
        '2016-01-17~2016-01-23',
    ]
    assert sorted(list(profile['financial']['time_frames'].keys())) == keys

    for key in ['contractor', 'non-contractor', 'additional']:
        expected = financial[key]
        assert sum(v[key] for v in profile['financial']['time_frames'].values()) == expected


@pytest.mark.django_db
def test_product_people_costs():
    product = make_product()
    assert product.people_costs(
        start_date=start_date,
        end_date=end_date,
        contractor_only=True) == contractor_rate * man_days
    assert product.people_costs(
        start_date=start_date,
        end_date=end_date,
        non_contractor_only=True) == non_contractor_rate * man_days

    with pytest.raises(ValueError):
        product.people_costs(
            start_date=start_date,
            end_date=end_date,
            non_contractor_only=True,
            contractor_only=True
        )


@pytest.mark.django_db
def test_product_costs():
    product = mommy.make(Product)
    mommy.make(
        Cost,
        product=product,
        start_date=date(2015, 1, 1),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        product=product,
        start_date=date(2016, 1, 1),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        product=product,
        start_date=date(2016, 1, 31),
        end_date=date(2018, 3, 31),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('55')
    )
    mommy.make(
        Cost,
        product=product,
        start_date=date(2016, 1, 3),
        type=COST_TYPES.ANNUALLY,
        cost=Decimal('60')
    )
    mommy.make(
        Cost,
        product=product,
        start_date=date(2018, 4, 30),
        end_date=date(2018, 7, 31),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('100')
    )

    assert product.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2016, 1, 2)) == Decimal('50')

    assert product.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2016, 1, 3)) == Decimal('110')

    assert product.additional_costs(
        start_date=date(2016, 1, 1),
        end_date=date(2017, 2, 3)) == Decimal('885')

    assert product.additional_costs(
        start_date=date(2018, 4, 30),
        end_date=date(2018, 7, 31)) == Decimal('400')


@pytest.mark.django_db
def test_product_visible():
    visible_area = mommy.make(Area, visible=True)
    invisible_area = mommy.make(Area, visible=False)

    p1 = mommy.make(Product, visible=True, area=visible_area)
    p2 = mommy.make(Product, visible=True)

    mommy.make(Product, visible=False, area=visible_area)
    mommy.make(Product, visible=False, area=invisible_area)
    mommy.make(Product, visible=True, area=invisible_area)
    mommy.make(Product, visible=False)

    assert {p.id for p in Product.objects.visible()} == {p1.id, p2.id}


@pytest.mark.django_db
def test_product_time_spent_for_product_with_tasks():
    product = make_product()
    assert product.time_spent() == 8  # no start_date nor end_date
    assert product.time_spent(start_date=start_date) == 8  # no end_date
    assert product.time_spent(end_date=end_date) == 8  # no end_date
    assert product.time_spent(
        start_date=start_date,
        end_date=end_date) == 8  # with both start_date and end_date


@pytest.mark.django_db
def test_product_current_fte():
    product = make_product()
    assert product.current_fte() == 0  # no work has been done in the last week
    time_spent = product.time_spent()
    workdays = get_workdays(start_date, end_date)
    assert product.current_fte(start_date, end_date) == time_spent / workdays


@pytest.mark.django_db
def test_product_status():
    product = make_product()
    assert product.status() is None

    today = date.today()
    date_1 = today - timedelta(days=100)
    date_2 = today - timedelta(days=50)
    date_3 = today + timedelta(days=50)
    status1 = mommy.make(
        ProductStatus, product=product, status=STATUS_TYPES.OK,
        start_date=date_1)
    status2 = mommy.make(
        ProductStatus, product=product, status=STATUS_TYPES.AT_RISK,
        start_date=date_2)
    status3 = mommy.make(
        ProductStatus, product=product, status=STATUS_TYPES.IN_TROUBLE,
        start_date=date_3)

    assert product.status(on=date_1) == status1
    assert product.status(on=date_1 + timedelta(days=25)) == status1
    assert product.status(on=date_2) == status2
    assert product.status() == status2
    assert product.status(on=today) == status2
    assert product.status(on=today - timedelta(days=25)) == status2
    assert product.status(on=today + timedelta(days=25)) == status2
    assert product.status(on=today + timedelta(days=75)) == status3


@pytest.mark.django_db
def test_product_budget():
    product = make_product()
    assert product.budget() == 0

    today = date.today()
    date_1 = today - timedelta(days=100)
    date_2 = today - timedelta(days=50)
    date_3 = today + timedelta(days=50)
    budget1 = mommy.make(
        Budget, product=product, budget=1000, start_date=date_1)
    budget2 = mommy.make(
        Budget, product=product, budget=1500, start_date=date_2)
    budget3 = mommy.make(
        Budget, product=product, budget=2000, start_date=date_3)

    assert product.budget(on=date_1) == budget1.budget
    assert product.budget(on=date_1 + timedelta(days=25)) == budget1.budget
    assert product.budget(on=date_2) == budget2.budget
    assert product.budget() == budget2.budget
    assert product.budget(on=today) == budget2.budget
    assert product.budget(on=today - timedelta(days=25)) == budget2.budget
    assert product.budget(on=today + timedelta(days=25)) == budget2.budget
    assert product.budget(on=today + timedelta(days=75)) == budget3.budget


@pytest.mark.django_db
def test_product_cost():
    product = make_product()
    cost = Decimal('50')
    mommy.make(
        Cost,
        product=product,
        start_date=start_date + timedelta(days=1),
        type=COST_TYPES.ONE_OFF,
        cost=cost
    )
    expected = (
        contractor_rate * man_days + non_contractor_rate * man_days + cost)
    assert product.cost_to_date == expected
    assert product.total_cost == expected

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
        product=product,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=7),
        days=2  # 2 working days in a future 7 day period
    )
    mommy.make(
        Cost,
        product=product,
        start_date=date.today() + timedelta(days=100),
        type=COST_TYPES.ONE_OFF,
        cost=cost
    )
    assert product.cost_to_date == expected
    assert product.total_cost == expected + contractor_rate * 2 + cost


@pytest.mark.django_db
def test_product_first_date():
    product = make_product()

    first_task_start_date = parse_date(task_time_ranges[0][0])
    # without discover date,
    # first date is the start date of the first task
    assert product.first_date == first_task_start_date

    # with discover date before first task,
    # first date is the discovery date
    discovery_date = first_task_start_date - timedelta(days=1)
    product.discovery_date = discovery_date
    assert product.first_date == discovery_date

    # with discover date before first task,
    # first date is the start date of the first task
    discovery_date = first_task_start_date + timedelta(days=1)
    product.discovery_date = discovery_date
    assert product.first_date == first_task_start_date

    # without tasks,
    # first date is the discovery date
    product2 = mommy.make(Product)
    product2.discovery_date = date.today()
    assert product2.first_date == product2.discovery_date


@pytest.mark.django_db
def test_product_last_date():
    product = make_product()
    last_task_end_date = parse_date(task_time_ranges[-1][-1])

    # without product end date,
    # last date is the end date of the first task
    assert product.last_date == last_task_end_date

    # with product end date after end date of last task,
    # first date is the discovery date
    end_date = last_task_end_date + timedelta(days=1)
    product.end_date = end_date
    assert product.last_date == end_date

    # with product end date before end date of last task,
    # first date is the discovery date
    end_date = last_task_end_date - timedelta(days=1)
    product.end_date = end_date
    assert product.last_date == last_task_end_date

    # without tasks,
    # first date is the end date
    product2 = mommy.make(Product)
    product2.end_date = date.today()
    assert product2.last_date == product2.end_date


@pytest.mark.django_db
def test_product_phase():

    product = mommy.make(Product)
    assert product.phase == 'Not Defined'

    product.discovery_date = date.today() - timedelta(days=1)
    assert product.phase == 'Discovery'

    product.alpha_date = date.today() - timedelta(days=1)
    assert product.phase == 'Alpha'

    product.beta_date = date.today() - timedelta(days=1)
    assert product.phase == 'Beta'

    product.live_date = date.today() - timedelta(days=1)
    assert product.phase == 'Live'

    product.end_date = date.today() - timedelta(days=1)
    assert product.phase == 'Ended'


@pytest.mark.django_db
def test_first_date():
    product = make_product()

    first_task_start_date = parse_date(task_time_ranges[0][0])

    # without budget or cost, the first task start date
    # is the default start date.
    assert product.first_date == first_task_start_date

    # with a cost after the first task, the first task start date
    # is still the default start date.
    first_cost_start_date = first_task_start_date + timedelta(days=2)
    mommy.make(
        Cost,
        product=product,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert product.first_date == first_task_start_date

    # with a cost before the first task, the first cost start date
    # is the default start date.
    first_cost_start_date = first_task_start_date - timedelta(days=2)
    mommy.make(
        Cost,
        product=product,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert product.first_date == first_cost_start_date

    # with a budget allocated after the first cost, the first cost
    # start date is the default start date
    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=product.first_date + timedelta(days=2))
    assert product.first_date == first_cost_start_date

    # with a budget allocated before the first cost, the budget
    # start date is the default start date
    first_budget_start_date = product.first_date - timedelta(days=2)
    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=first_budget_start_date)
    assert product.first_date == first_budget_start_date


@pytest.mark.django_db
def test_last_date():
    product = make_product()

    last_task_end_date = parse_date(task_time_ranges[-1][-1])

    # without budget or cost, the last task end date
    # is the default start date.
    assert product.last_date == last_task_end_date

    # with a cost before the last task, the last task end date
    # is still the default start date.
    first_cost_start_date = last_task_end_date - timedelta(days=2)
    last_cost_start_date = last_task_end_date - timedelta(days=1)
    mommy.make(
        Cost,
        product=product,
        start_date=first_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    mommy.make(
        Cost,
        product=product,
        start_date=last_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert product.last_date == last_task_end_date

    # with a cost after the last task, the last cost start date
    # is the default end date.
    last_cost_start_date = last_task_end_date + timedelta(days=1)
    mommy.make(
        Cost,
        product=product,
        start_date=last_cost_start_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert product.last_date == last_cost_start_date

    # with an end date for the last cost, the end date of the
    # last cost is the default end date.
    last_cost_end_date = last_cost_start_date + timedelta(days=2)
    mommy.make(
        Cost,
        product=product,
        start_date=last_cost_start_date - timedelta(days=1),
        end_date=last_cost_end_date,
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('50')
    )
    assert product.last_date == last_cost_end_date

    # with a budget allocated before the last cost, the cost
    # start date is the default end date
    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=last_cost_start_date - timedelta(days=2))
    assert product.last_date == last_cost_end_date

    # with a budget allocated after the last cost, the budget
    # start date is the default end date
    last_budget_start_date = product.last_date + timedelta(days=2)
    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=last_budget_start_date)
    assert product.last_date == last_budget_start_date


@pytest.mark.django_db
def test_last_date_no_dates():
    product = mommy.make(Product)
    with pytest.raises(ValueError):
        product.last_date


@pytest.mark.django_db
def test_product_financial_rag():
    product = mommy.make(Product)
    assert product.financial_rag == 'GREEN'

    mommy.make(
        Budget,
        product=product,
        budget=1000,
        start_date=date.today()
    )
    assert product.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        product=product,
        start_date=date.today() - timedelta(days=2),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('500')
    )
    assert product.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        product=product,
        start_date=date.today() + timedelta(days=2),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('500')
    )
    assert product.financial_rag == 'GREEN'

    mommy.make(
        Cost,
        product=product,
        start_date=date.today() + timedelta(days=4),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('100')
    )
    assert product.financial_rag == 'AMBER'

    mommy.make(
        Cost,
        product=product,
        start_date=date.today() + timedelta(days=5),
        type=COST_TYPES.ONE_OFF,
        cost=Decimal('1')
    )
    assert product.financial_rag == 'RED'


@pytest.mark.django_db
def test_admin_url():
    product = make_product()
    expected = '/admin/dashboard/product/{}/change/'.format(product.id)
    assert product.admin_url == expected


@pytest.mark.django_db
def test_non_contractor_salary_costs():
    product = make_product()
    contractor = mommy.make(Person, is_contractor=True)
    non_contractor = mommy.make(Person, is_contractor=False)
    # 20 working days
    start_date = date(2017, 2, 1)
    end_date = date(2017, 2, 28)
    today = date(2017, 2, 18)
    mommy.make(
        Rate,
        start_date=today - timedelta(days=30),
        rate=Decimal('80'),
        person=contractor
    )
    mommy.make(
        Rate,
        start_date=today - timedelta(days=30),
        rate=Decimal('120'),
        person=non_contractor
    )
    mommy.make(
        Task,
        person=contractor,
        product=product,
        start_date=today - timedelta(days=7),
        end_date=today - timedelta(days=1),
        days=2
    )
    mommy.make(
        Task,
        person=non_contractor,
        product=product,
        start_date=today - timedelta(days=7),
        end_date=today - timedelta(days=1),
        days=2
    )
    mommy.make(
        PersonCost,
        person=non_contractor,
        name='ASLC',
        start_date=start_date,
        end_date=end_date,
        type=COST_TYPES.MONTHLY,
        cost=Decimal('20')
    )

    assert product.people_additional_costs(start_date, end_date) == Decimal('2')

    assert product.people_costs(start_date, end_date) == Decimal('402')

    assert product.non_contractor_salary_costs(start_date, end_date) == Decimal('240')
