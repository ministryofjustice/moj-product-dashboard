# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField

from dashboard.libs.date_tools import (
    get_workdays, get_overlap, get_weekly_repeat_time_windows)


class TaskManager(models.Manager):
    use_for_related_fields = True

    def between(self, start_date=None, end_date=None):
        """"
        retrieve all tasks, which has any time spent in a time window defined
        by the start date and end date. the following types are all included:
        1. tasks starting in the time window
        2. tasks ending in the time window
        3. tasks running through the entire time window
        :param start_date: a date object for the start of the time window
        :param end_date: a date object for the end of the time window
        """
        latest_repeating_task_start_date = (
            start_date - (models.F('end_date') - models.F('start_date')))
        if start_date and end_date:
            query = (
                # non repeating tasks
                models.Q(repeat_state=0) &
                models.Q(start_date__lte=end_date) &
                models.Q(end_date__gte=start_date)
            ) | (
                # repeating tasks
                models.Q(repeat_state__gt=0) &
                models.Q(start_date__lte=end_date) &
                models.Q(repeat_end__gte=latest_repeating_task_start_date)
            )
        elif start_date:
            query = (
                # non repeating tasks
                models.Q(repeat_state=0) &
                models.Q(end_date__gte=start_date)
            ) | (
                # repeating tasks
                models.Q(repeat_state__gt=0) &
                models.Q(repeat_end__gte=latest_repeating_task_start_date)
            )
        elif end_date:
            query = models.Q(start_date__lte=end_date)
        else:
            query = models.Q()
        return self.filter(query)


class Task(models.Model):
    NO_REPEAT = 0
    WEEKLY = 1
    MONTHLY = 2
    REPEAT_MODE_CHOICES = (
        (NO_REPEAT, 'no repeat'),
        (WEEKLY, 'weekly'),
        (MONTHLY, 'monthly'),
    )
    name = models.CharField(max_length=128, null=True)
    person = models.ForeignKey('Person', related_name='tasks')
    product = models.ForeignKey('Product', related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    repeat_state = models.PositiveSmallIntegerField(
        choices=REPEAT_MODE_CHOICES,
        default=NO_REPEAT)
    repeat_end = models.DateField(null=True)
    # days is the cumulative number of days of a task.
    # if a task is worked on for 2 hours per day for 4 days,
    # the value of days is 1.
    days = models.DecimalField(max_digits=10, decimal_places=5)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField(null=True)
    objects = TaskManager()

    def __str__(self):
        if self.name:
            result = '{} - {} on {} from {} to {} for {:.2g} days'.format(
                self.name, self.person, self.product,
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'),
                self.days)
        else:
            result = '{} on {} from {} to {} for {:.2g} days'.format(
                self.person, self.product,
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'),
                self.days)
        if self.repeat_state == 1:
            result = '{} and repeat weekly until {}'.format(
                result, self.repeat_end.strftime('%Y-%m-%d'))
        return result

    @property
    def workdays(self):
        """
        number of workdays for the task. it's the number for days
        from start_date to end_date minus holidays.
        """
        return get_workdays(self.start_date, self.end_date)

    def non_repeat_task_time_spent(self, start_date, end_date):
        overlap = get_overlap(
            (start_date, end_date),
            (self.start_date, self.end_date)
        )

        if not overlap:
            return Decimal('0')
        if overlap == (self.start_date, self.end_date):
            return self.days

        timewindow_workdays = get_workdays(*overlap)

        return Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days

    def weekly_repeat_task_time_spent(self, start_date, end_date):
        repeat_time_windows = get_weekly_repeat_time_windows(
            self.start_date, self.end_date, self.repeat_end)
        days = Decimal('0')
        for time_window in repeat_time_windows:
            overlap = get_overlap((start_date, end_date), time_window)
            if not overlap:
                continue
            if overlap == (self.start_date, self.end_date):
                days += self.days
                continue
            timewindow_workdays = get_workdays(*overlap)
            days += Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days
        return days

    def non_repeat_task_people_costs(self, start_date, end_date,
                                     additional_cost_name):
        overlap = get_overlap(
            (start_date, end_date), (self.start_date, self.end_date))

        if not overlap:
            return Decimal('0')

        if additional_cost_name:
            rate = self.person.additional_rate(*overlap,
                                               name=additional_cost_name)
        else:
            rate = self.person.rate_between(*overlap)
        if not rate:
            return Decimal('0')

        return rate * self.get_days(*overlap)

    def weekly_repeat_task_people_costs(self, start_date, end_date,
                                        additional_cost_name):
        repeat_time_windows = get_weekly_repeat_time_windows(
            self.start_date, self.end_date, self.repeat_end)
        spent = Decimal('0')
        for time_window in repeat_time_windows:
            overlap = get_overlap((start_date, end_date), time_window)
            if not overlap:
                continue
            if additional_cost_name:
                rate = self.person.additional_rate(*overlap,
                                                   name=additional_cost_name)
            else:
                rate = self.person.rate_between(*overlap)
            if not rate:
                continue
            spent += rate * self.get_days(*overlap)
        return spent

    def time_spent(self, start_date=None, end_date=None):
        """
        get the days spent on the task during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :return: number of days, a decimal
        """
        start_date = start_date or self.start_date
        if not end_date:
            if self.repeat_state == 0:
                end_date = self.end_date
            else:
                # repeat_end determins the last repeated start_date
                end_date = self.end_date - self.start_date + self.repeat_end

        #  special cases
        if start_date > end_date or end_date < self.start_date or self.workdays == 0:
            return Decimal('0')

        # repeating weekly
        if self.repeat_state == 1:
            return self.weekly_repeat_task_time_spent(start_date, end_date)
        # NOTE this means repeat_state == 2 (monthly) is treated as a
        # non repeat task. the reason is Float's behavour for monthly
        # repeat task is not consistent.
        #  For example, here are two tasks both repeating monthly.
        #  1) start date: 2017-03-01, end date: 2017-03-01
        #  2) start date: 2017-03-08, end date: 2017-03-08
        # Although the first occurrences are one week apart,
        # both their repetitions are on 2017-04-05, 2017-05-03,
        # 2017-06-07 etc
        return self.non_repeat_task_time_spent(start_date, end_date)

    def people_costs(self, start_date=None, end_date=None,
                     additional_cost_name=None, calculation_start_date=None):
        """
        get the money spent on the task during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :param additional_cost_name: name of specific additional cost to total
        :return: cost in pound, a decimal
        """
        start_date = start_date or self.start_date
        if not end_date:
            if self.repeat_state == 0:
                end_date = self.end_date
            else:
                # repeat_end determins the last repeated start_date
                end_date = self.repeat_end + (self.end_date - self.start_date)

        #  special cases
        if start_date > end_date or end_date < self.start_date or self.workdays == 0:
            return Decimal('0')

        # task before calculation_start_date
        if calculation_start_date:
            if calculation_start_date > end_date:
                return Decimal('0')
            elif calculation_start_date > start_date:
                start_date = calculation_start_date
        if self.repeat_state == 0:
            return self.non_repeat_task_people_costs(
                start_date, end_date, additional_cost_name)
        if self.repeat_state == 1:
            return self.weekly_repeat_task_people_costs(
                start_date, end_date, additional_cost_name)
        return Decimal('0')

    def get_days(self, *timewindow):
        timewindow_workdays = get_workdays(*timewindow)
        return Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days
