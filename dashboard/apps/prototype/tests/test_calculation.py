from decimal import Decimal
from datetime import date

from django.test import TestCase
from model_mommy import mommy

from dashboard.apps.prototype.models import Person, Project, Task, Rate


class TaskTimeSpentTestCase(TestCase):

    def setUp(self):
        # task_0 is a task spanning over 9 calendar days. with a
        # weekend and bank holiday in the middle, the number of
        # actual working days is 6. given the time for the task is 3 days,
        # 0.5 day is spent daily during each of the 6 working days.
        self.task_0 = Task.objects.create(
            name='task_0', person_id=0, project_id=0, float_id=0,
            start_date=date(2016, 4, 27),
            end_date=date(2016, 5, 5),
            days=3
        )

        # task_1 is a task for bank holiday over Easter holiday
        self.task_1 = Task.objects.create(
            name='day off over Easter', person_id=0, project_id=1,
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
        self.billable_project = mommy.make(
            Project, is_billable=True)
        self.non_billable_project = mommy.make(
            Project, is_billable=False)
        self.person = mommy.make(Person)
        mommy.make(Rate, start_date=date(2015, 1, 1), rate=Decimal('400'),
                   person=self.person)
        self.non_billable_task = mommy.make(
            Task, project=self.non_billable_project,
            start_date=date(2016, 6, 1),
            end_date=date(2016, 6, 10),
            days=8)
        self.billable_task = mommy.make(
            Task, project=self.billable_project,
            person=self.person,
            start_date=date(2016, 6, 1),
            end_date=date(2016, 6, 10),
            days=8)

    def test_non_billable_task_spending(self):
        assert self.non_billable_task.money_spent() == 0

    def test_billable_task_total_spending(self):
        assert self.billable_task.money_spent() == 400 * 8

    def test_billable_task_weekday_spending(self):
        assert self.billable_task.money_spent(
            date(2016, 6, 1), date(2016, 6, 3)) == 400 * 3

    def test_billable_task_weekend_spending_is_zero(self):
        assert self.billable_task.money_spent(
            date(2016, 6, 4), date(2016, 6, 5)) == 0

    def test_billable_task_weekday_plus_weekend_spending(self):
        assert self.billable_task.money_spent(
            date(2016, 6, 1), date(2016, 6, 5)) == 400 * 3
