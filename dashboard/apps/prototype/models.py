# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import JSONField

from dashboard.libs.date_tools import get_workdays


class Person(models.Model):
    float_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    email = models.EmailField(null=True)
    avatar = models.URLField(null=True)
    roles = models.ManyToManyField('Role', through='PersonRole')
    raw_data = JSONField()

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=32)
    people = models.ManyToManyField('Person', through='PersonRole')
    default_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_contractor = models.BooleanField()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'is_contractor')


class Rate(models.Model):
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    person = models.ForeignKey('Person', related_name='rates')
    start_date = models.DateField()

    def __str__(self):
        return '"{}" @ "{}"/day from "{}"'.format(
            self.person, self.amount, self.start_date)


class PersonRole(models.Model):
    person = models.ForeignKey('Person')
    role = models.ForeignKey('Role')
    start_date = models.DateField()

    def __str__(self):
        return '"{}" "{}" from "{}"'.format(
            self.role, self.person, self.start_date)


class Client(models.Model):
    name = models.CharField(max_length=32)
    float_id = models.CharField(max_length=64, unique=True)
    raw_data = JSONField()

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField()
    float_id = models.CharField(max_length=64, unique=True)
    is_billable = models.BooleanField()
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
    name = models.CharField(max_length=64, null=True)
    person = models.ForeignKey('Person', related_name='tasks')
    project = models.ForeignKey('Project', related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=10, decimal_places=5)
    float_id = models.CharField(max_length=64, unique=True)
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

        return (slice_workdays / self.workdays) * self.days
