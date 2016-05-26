# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy

from dashboard.libs.date_tools import get_workdays
from dashboard.libs.rate_converter import RATE_TYPES, RateConverter


class Person(models.Model):
    float_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    email = models.EmailField(null=True)
    avatar = models.URLField(null=True)
    is_contractor = models.BooleanField(default=False)
    job_title = models.CharField(max_length=128, null=True)
    is_current = models.BooleanField(default=True)
    raw_data = JSONField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = ugettext_lazy('People')


class Rate(models.Model):
    rate_type = models.PositiveSmallIntegerField(
        choices=RATE_TYPES, default=RATE_TYPES.DAY)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    person = models.ForeignKey('Person', related_name='rates')
    start_date = models.DateField()

    def __str__(self):
        return '"{}" @ "{}"/{} from "{}"'.format(
            self.person, self.rate,
            RATE_TYPES.from_value(self.rate_type).display, self.start_date)

    class Meta:
        ordering = ('-start_date',)
        unique_together = ('start_date', 'person')

    def average_day_rate(self, start_date=None, end_date=None, on=None):
        """
        average day rate in range
        param: start_date: date object - beginning of time period for average
        param: end_date: date object - end of time period for average
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - average day rate
        """
        return RateConverter(
            rate=self.rate,
            rate_type=self.rate_type
        ).average_day_rate(start_date, end_date, on)


class Client(models.Model):
    name = models.CharField(max_length=128)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField()

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    float_id = models.CharField(max_length=128, unique=True)
    is_billable = models.BooleanField(default=True)
    project_manager = models.ForeignKey(
        'Person', related_name='projects', null=True)
    client = models.ForeignKey('Client', related_name='projects', null=True)
    discovery_date = models.DateField(null=True)
    alpha_date = models.DateField(null=True)
    beta_date = models.DateField(null=True)
    live_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    raw_data = JSONField()

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=128, null=True)
    person = models.ForeignKey('Person', related_name='tasks')
    project = models.ForeignKey('Project', related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=10, decimal_places=5)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField()

    def __str__(self):
        if self.name:
            return '{} - {} on {} from {} to {} for {:.2g} days'.format(
                self.name, self.person, self.project,
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d'),
                self.days)
        else:
            return '{} on {} from {} to {} for {:.2g} days'.format(
                self.person, self.project,
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

        if start_date < self.start_date:
            if end_date < self.start_date:
                slice = None
            elif end_date <= self.end_date:
                slice = self.start_date, end_date
            else:
                slice = self.start_date, self.end_date
        elif start_date <= self.end_date:
            if end_date <= self.end_date:
                slice = start_date, end_date
            else:
                slice = start_date, self.end_date
        else:
            slice = None

        if not slice:
            return 0
        if slice == (self.start_date, self.end_date):
            return self.days

        slice_workdays = get_workdays(*slice)

        return Decimal(slice_workdays) / Decimal(self.workdays) * self.days
