# -*- coding: utf-8 -*-
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy

from dashboard.libs.date_tools import get_workdays, get_overlap
from dashboard.libs.rate_converter import RATE_TYPES, RateConverter, \
    dec_workdays, average_rate_from_segments


class Person(models.Model):
    float_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    email = models.EmailField(null=True)
    avatar = models.URLField(null=True)
    is_contractor = models.BooleanField(default=False)
    job_title = models.CharField(max_length=128, null=True)
    is_current = models.BooleanField(default=True)
    raw_data = JSONField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = ugettext_lazy('People')

    def rate_between(self, start_date, end_date):
        """
        average day rate in range
        param: start_date: date object - beginning of time period for average
        param: end_date: date object - end of time period for average
        return: Decimal object - average day rate
        """
        rate_list = self.rates.between(start_date, end_date)
        segments = []
        for n, rate in enumerate(rate_list):
            start = rate.start_date
            try:
                end = rate_list[n + 1].start_date - timedelta(days=1)
            except IndexError:
                end = end_date
            segments.append(
                (start, end, rate.rate_between(start, end))
            )

        total_workdays = dec_workdays(start_date, end_date)

        return average_rate_from_segments(segments, total_workdays)

    def rate_on(self, on=None):
        """
        rate at time of date
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - rate on date
        """
        rate = self.rates.on(on=on)
        return rate.rate_on(on) if rate else None


class RatesManager(models.Manager):
    use_for_related_fields = True

    def on(self, on):
        return self.get_queryset()\
            .filter(start_date__lte=on)\
            .order_by('-start_date')\
            .first()

    def between(self, start_date, end_date):
        rates = list(self.get_queryset().
                     filter(start_date__lte=end_date,
                            start_date__gt=start_date)
                     .order_by('start_date'))
        first = self.on(start_date)
        if first:
            rates.insert(0, first)
        return rates


class Rate(models.Model):
    rate_type = models.PositiveSmallIntegerField(
        choices=RATE_TYPES, default=RATE_TYPES.DAY)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    person = models.ForeignKey('Person', related_name='rates')
    start_date = models.DateField()

    objects = RatesManager()

    def __str__(self):
        return '"{}" @ "{}"/{} from "{}"'.format(
            self.person, self.rate,
            RATE_TYPES.for_value(self.rate_type).display, self.start_date)

    class Meta:
        ordering = ('-start_date',)
        unique_together = ('start_date', 'person')

    @property
    def converter(self):
        return RateConverter(
            rate=self.rate,
            rate_type=self.rate_type
        )

    def rate_between(self, start_date, end_date):
        """
        average day rate in range
        param: start_date: date object - beginning of time period for average
        param: end_date: date object - end of time period for average
        return: Decimal object - average day rate
        """
        return self.converter.rate_between(start_date, end_date)

    def rate_on(self, on=None):
        """
        rate at time of date
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - rate on date
        """
        return self.converter.rate_on(on)


class Client(models.Model):
    name = models.CharField(max_length=128)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField(null=True)

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
    raw_data = JSONField(null=True)

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
    raw_data = JSONField(null=True)

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

        # sanitise the time window
        if start_date >= self.end_date:
            end_date = start_date
        if end_date <= self.start_date:
            start_date = end_date

        # we shouldn't have these, but it can happen
        # where some tasks spread over holidays only
        if self.workdays == 0:
            return 0

        timewindow = get_overlap(
            (start_date, end_date), (self.start_date, self.end_date))

        if not timewindow:
            return 0
        if timewindow == (self.start_date, self.end_date):
            return self.days

        timewindow_workdays = get_workdays(*timewindow)

        return Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days

    def money_spent(self, start_date=None, end_date=None):
        """
        get the money spent on the task during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :return: cost in pound, a decimal
        """
        start_date = start_date or self.start_date
        end_date = end_date or self.end_date

        timewindow = get_overlap(
            (start_date, end_date), (self.start_date, self.end_date))

        if not timewindow:
            return 0

        rate = self.person.rate_between(*timewindow)
        if not rate:
            return 0
        timewindow_workdays = get_workdays(*timewindow)
        days = Decimal(timewindow_workdays) / Decimal(self.workdays) * self.days
        return rate * days
