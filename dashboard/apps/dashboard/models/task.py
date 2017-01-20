# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField

from dashboard.libs.date_tools import get_workdays, get_overlap


class TaskManager(models.Manager):
    use_for_related_fields = True

    def between(self, start_date, end_date):
        """"
        retrieve all tasks, which has any time spent in a time window defined
        by the start date and end date. the following types are all included:
        1. tasks starting in the time window
        2. tasks ending in the time window
        3. tasks running through the entire time window
        :param start_date: a date object for the start of the time window
        :param end_date: a date object for the end of the time window
        """
        return self.filter(
            models.Q(start_date__gte=start_date, start_date__lte=end_date) |
            models.Q(end_date__gte=start_date, end_date__lte=end_date) |
            models.Q(start_date__lt=start_date, end_date__gt=end_date)
        )


class Task(models.Model):
    name = models.CharField(max_length=128, null=True)
    person = models.ForeignKey('Person', related_name='tasks')
    product = models.ForeignKey('Product', related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=10, decimal_places=5)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField(null=True)
    objects = TaskManager()

    def __str__(self):
        if self.name:
            return '{} - {} on {} from {} to {} for {:.2g} days'.format(
                self.name, self.person, self.product,
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'),
                self.days)
        else:
            return '{} on {} from {} to {} for {:.2g} days'.format(
                self.person, self.product,
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'),
                self.days)

    @property
    def workdays(self):
        """
        number of workdays for the task. it's the number for days
        from start_date to end_date minus holidays.
        """
        return get_workdays(self.start_date, self.end_date)

    def time_spent(self, start_date=None, end_date=None):
        """
        get the days spent on the task during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :return: number of days, a decimal
        """
        start_date = start_date or self.start_date
        end_date = end_date or self.end_date

        # sanitise the time window
        if start_date >= self.end_date:
            end_date = start_date
        if end_date <= self.start_date:
            start_date = end_date

        # we shouldn't have these, but it can happen
        # where some tasks spread over holidays only
        if self.workdays == 0:
            return Decimal('0')

        timewindow = get_overlap(
            (start_date, end_date), (self.start_date, self.end_date))

        if not timewindow:
            return Decimal('0')
        if timewindow == (self.start_date, self.end_date):
            return self.days

        timewindow_workdays = get_workdays(*timewindow)

        return Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days

    def people_costs(self, start_date=None, end_date=None,
                     additional_cost_name=None):
        """
        get the money spent on the task during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :param additional_cost_name: name of specific additional cost to total
        :return: cost in pound, a decimal
        """
        start_date = start_date or self.start_date
        end_date = end_date or self.end_date

        timewindow = get_overlap(
            (start_date, end_date), (self.start_date, self.end_date))

        if not timewindow:
            return Decimal('0')

        if additional_cost_name:
            rate = self.person.additional_rate(*timewindow,
                                               name=additional_cost_name)
        else:
            rate = self.person.rate_between(*timewindow)
        if not rate:
            return Decimal('0')

        return rate * self.get_days(*timewindow)

    def get_days(self, *timewindow):
        timewindow_workdays = get_workdays(*timewindow)
        return Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days
