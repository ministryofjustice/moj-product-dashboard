from decimal import Decimal
from datetime import date

from django.test import TestCase

from dashboard.apps.prototype.models import Task


class TaskTimeSpentTestCase(TestCase):

    def setUp(self):
        # task_0 is a task spanning over 9 calendar days. with a
        # weekend and bank holiday in the middle, the number of
        # actual working days is 6. given the time for the task is 3 days,
        # 0.5 day is spent daily during each of the 6 working days.
        self.task_0 = Task.objects.create(
            name='task_0', person_id=0, project_id=0,
            start_date=date(2016, 4, 27),
            end_date=date(2016, 5, 5),
            days=3,
            raw_data={}
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
