from decimal import Decimal
from datetime import date

from django.test import TestCase
from model_mommy import mommy
from faker import Faker
import pytest

from dashboard.apps.dashboard.models import Person, Product, Task, Rate
from dashboard.libs.date_tools import parse_date, to_datetime


class TaskTimeSpentTestCase(TestCase):

    def setUp(self):
        # task_0 is a task spanning over 9 calendar days. with a
        # weekend and bank holiday in the middle, the number of
        # actual working days is 6. given the time for the task is 3 days,
        # 0.5 day is spent daily during each of the 6 working days.
        self.task_0 = Task.objects.create(
            name='task_0', person_id=0, product_id=0, float_id=0,
            start_date=date(2016, 4, 27),
            end_date=date(2016, 5, 5),
            days=3
        )

        # task_1 is a task for bank holiday over Easter holiday
        self.task_1 = Task.objects.create(
            name='day off over Easter', person_id=0, product_id=1,
            float_id=1,
            start_date=date(2016, 3, 25),
            end_date=date(2016, 3, 28),
            days=2
        )

    def test_no_time_window_specified(self):
        days = self.task_0.time_spent()
        self.assertEqual(days, self.task_0.days)

    def test_time_window_covers_entire_task_span(self):
        days = self.task_0.time_spent(start_date=date(2016, 4, 1),
                                      end_date=date(2016, 6, 1))
        self.assertEqual(days, self.task_0.days)

    def test_time_window_no_overlapping(self):
        days = self.task_0.time_spent(start_date=date(2016, 6, 1))
        self.assertEqual(days, 0)

        days = self.task_0.time_spent(end_date=date(2016, 4, 1))
        self.assertEqual(days, 0)

    def test_time_window_slices_head_of_task(self):
        days = self.task_0.time_spent(start_date=date(2016, 4, 15),
                                      end_date=date(2016, 4, 30))
        self.assertEqual(days, Decimal('1.5'))

    def test_time_window_slices_tail_of_task(self):
        days = self.task_0.time_spent(start_date=date(2016, 5, 3),
                                      end_date=date(2016, 6, 3))
        self.assertEqual(days, Decimal('1.5'))

    def test_bank_holiday(self):
        days = self.task_0.time_spent(start_date=date(2016, 4, 15),
                                      end_date=date(2016, 5, 2))
        self.assertEqual(days, Decimal('1.5'))

    def test_bank_holiday_only(self):
        days = self.task_1.time_spent(start_date=date(2016, 3, 25),
                                      end_date=date(2016, 3, 25))
        self.assertEqual(days, Decimal('0'))


class TaskMoneySpentTestCase(TestCase):

    def setUp(self):
        person = mommy.make(Person)
        mommy.make(Rate, start_date=date(2015, 1, 1), rate=Decimal('400'),
                   person=person)
        self.task_0 = mommy.make(
            Task, product=mommy.make(Product),
            person=person,
            start_date=date(2016, 6, 1),
            end_date=date(2016, 6, 10),
            days=8)

    def test_task_total_spending(self):
        assert self.task_0.people_costs() == 400 * 8

    def test_task_weekday_spending(self):
        assert self.task_0.people_costs(
            date(2016, 6, 1), date(2016, 6, 3)) == 400 * 3

    def test_task_weekend_spending_is_zero(self):
        assert self.task_0.people_costs(
            date(2016, 6, 4), date(2016, 6, 5)) == 0

    def test_task_weekday_plus_weekend_spending(self):
        assert self.task_0.people_costs(
            date(2016, 6, 1), date(2016, 6, 5)) == 400 * 3

    def test_task_spending_after_end_date_is_zero(self):
        assert self.task_0.people_costs(
            date(2016, 6, 11), date(2016, 6, 12)) == 0

    def test_task_spending_before_staart_date_is_zero(self):
        assert self.task_0.people_costs(
            date(2016, 5, 25), date(2016, 5, 31)) == 0


rate1 = Decimal('400')
rate2 = Decimal('500')
rate3 = Decimal('600')


@pytest.mark.parametrize("sday,eday,expected", [
    (17, 17, rate1 * 1),
    (17, 18, rate1 * 2),
    (17, 19, rate1 * 3),
    (17, 20, rate1 * 4),
    (17, 21, rate1 * 4),
    (17, 22, rate1 * 4),
    (17, 23, rate1 * 4 + rate2 * 1),
    (17, 24, rate1 * 4 + rate2 * 2),
    (17, 25, rate1 * 4 + rate2 * 3),
    (17, 26, rate1 * 4 + rate2 * 4),
    (17, 27, rate1 * 4 + rate2 * 5),
    (17, 28, rate1 * 4 + rate2 * 5),
    (17, 29, rate1 * 4 + rate2 * 5),
    (17, 30, rate1 * 4 + rate2 * 5),
    (17, 31, rate1 * 4 + rate2 * 5 + rate3),

    (22, 22, rate2 * 0),
    (22, 23, rate2 * 1),
    (22, 24, rate2 * 2),
    (22, 25, rate2 * 3),
    (22, 26, rate2 * 4),
    (22, 27, rate2 * 5),
    (22, 28, rate2 * 5),
    (22, 29, rate2 * 5),
    (22, 30, rate2 * 5),
    (22, 31, rate2 * 5 + rate3),
])
@pytest.mark.django_db
def test_multiple_rates(sday, eday, expected):
    """
                    May 2016
               Su Mo Tu We Th Fr Sa
    400/day     1  2  3  4  5  6  7
    400/day     8  9 10 11 12 13 14
    400/day    15 16 17 18 19 20 21
    500/day    22 23 24 25 26 27 28
    600/day    29 30 31

    task starts from 17th, lasts for 10 working days and ends on 31st.
    30th is a bank holiday.
    """
    person = mommy.make(Person)
    mommy.make(Rate, start_date=date(2016, 5, 1), rate=rate1,
               person=person)  # 4 days of the task
    mommy.make(Rate, start_date=date(2016, 5, 22), rate=rate2,
               person=person)  # 5 days of the task
    mommy.make(Rate, start_date=date(2016, 5, 29), rate=rate3,
               person=person)  # 1 day of the task
    task_0 = mommy.make(
        Task, product=mommy.make(Product),
        person=person,
        start_date=date(2016, 5, 17),
        end_date=date(2016, 5, 31),
        days=10)

    people_cost = task_0.people_costs(
        date(2016, 5, sday), date(2016, 5, eday)
    )
    assert round(people_cost, 0) == expected


class TaskString(TestCase):

    def test_task_without_name(self):
        task_without_name = mommy.make(
            Task, product=mommy.make(Product, name='product 0'),
            person=mommy.make(Person, name='John'),
            start_date=date(2016, 6, 1),
            end_date=date(2016, 6, 10),
            days=8)
        expected = 'John on product 0 from 2016-06-01 to 2016-06-10 for 8 days'
        assert str(task_without_name) == expected

    def test_task_with_name(self):
        task_with_name = mommy.make(
            Task,
            name='task 0',
            product=mommy.make(Product, name='product 0'),
            person=mommy.make(Person, name='John'),
            start_date=date(2016, 6, 1),
            end_date=date(2016, 6, 10),
            days=8)
        expected = (
            'task 0 - John on product 0'
            ' from 2016-06-01 to 2016-06-10 for 8 days')
        assert str(task_with_name) == expected


year_start = parse_date('2016-01-01')
first_half_end = parse_date('2016-06-30')
second_half_start = parse_date('2016-07-01')
year_end = parse_date('2016-12-31')


class TestTaskManager(TestCase):

    def setUp(self):
        self.first_half_year_tasks = []
        self.second_half_year_tasks = []

        fake = Faker()

        # create 10 tasks for the 1st half year
        for _ in range(10):
            rand_sd = fake.date_time_between(
                to_datetime(year_start),
                to_datetime(first_half_end)
            )
            rand_ed = fake.date_time_between(
                rand_sd,
                to_datetime(first_half_end)
            )
            task = mommy.make(
                Task,
                start_date=rand_sd.date(),
                end_date=rand_ed.date()
            )
            self.first_half_year_tasks.append(task)

        # create another 10 tasks for the 2st half year
        for _ in range(10):
            rand_sd = fake.date_time_between(
                to_datetime(second_half_start),
                to_datetime(year_end)
            )
            rand_ed = fake.date_time_between(
                rand_sd,
                to_datetime(year_end)
            )

            task = mommy.make(
                Task,
                start_date=rand_sd.date(),
                end_date=rand_ed.date()
            )
            self.second_half_year_tasks.append(task)

    @staticmethod
    def assert_tasks_equals(tasks1, tasks2):
        t1_ids = [t.id for t in tasks1]
        t2_ids = [t.id for t in tasks2]
        assert sorted(t1_ids) == sorted(t2_ids)

    def test_all_tasks(self):
        all_tasks = self.first_half_year_tasks + self.second_half_year_tasks
        self.assert_tasks_equals(Task.objects.all(), all_tasks)

    def test_between(self):
        first_half_year_tasks = Task.objects.between(
            year_start, first_half_end)
        second_half_year_tasks = Task.objects.between(
            second_half_start, year_end)

        self.assert_tasks_equals(
            first_half_year_tasks, self.first_half_year_tasks)
        self.assert_tasks_equals(
            second_half_year_tasks, self.second_half_year_tasks)
