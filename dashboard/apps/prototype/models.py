# -*- coding: utf-8 -*-
from datetime import timedelta, date
from decimal import Decimal
from dateutil.rrule import MONTHLY, YEARLY

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import Q
from django.utils.translation import ugettext_lazy

from dashboard.libs.date_tools import (
    get_workdays, get_overlap, slice_time_window, dates_between)
from dashboard.libs.rate_converter import RATE_TYPES, RateConverter, \
    dec_workdays, average_rate_from_segments
from dashboard.libs.cache_tools import method_cache

from .constants import RAG_TYPES, COST_TYPES


class Person(models.Model):
    float_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    email = models.EmailField(null=True)
    avatar = models.URLField(null=True)
    is_contractor = models.BooleanField(
        default=False,
        verbose_name='is contractor?'
    )
    job_title = models.CharField(max_length=128, null=True)
    is_current = models.BooleanField(
        default=True,
        verbose_name='is current staff?'
    )
    raw_data = JSONField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = ugettext_lazy('People')
        permissions = (
            ('upload_person', 'Can upload monthly payroll'),
        )

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
        return '"{}" @ "{} {}" from "{}"'.format(
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

    class Meta:
        verbose_name = ugettext_lazy('service area')

    def __str__(self):
        return self.name

    def profile(self, project_ids=None, start_date=None, end_date=None,
                freq=None):
        """
        get the profile of a service area in a time window.
        :param project_ids: a list of project_ids, if the value is not
        specified, get all projects.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary representing the profile
        """
        projects = self.projects.filter(visible=True)
        if project_ids is not None:
            projects = projects.filter(id__in=project_ids)
        result = {
            'id': self.id,
            'name': self.name
        }
        result['projects'] = {
            project.id: project.profile(start_date, end_date, freq)
            for project in projects
        }
        return result


class ProjectManager(models.Manager):
    use_for_related_fields = True

    def visible(self):
        return self.get_queryset().filter(visible=True)


class Project(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    float_id = models.CharField(max_length=128, unique=True)
    is_billable = models.BooleanField(default=True)
    project_manager = models.ForeignKey(
        'Person', related_name='projects', null=True)
    client = models.ForeignKey('Client', related_name='projects', null=True)
    discovery_date = models.DateField(null=True, blank=True)
    alpha_date = models.DateField(null=True, blank=True)
    beta_date = models.DateField(null=True, blank=True)
    live_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    visible = models.BooleanField(default=True)
    raw_data = JSONField(null=True)

    objects = ProjectManager()

    @property
    def first_date(self):
        """
        first day in the project lifetime. it's the lesser of
        the discovery date and default start date.
        """
        candidates = []
        try:
            candidates.append(self.default_start_date)
        except ValueError:
            pass
        if self.discovery_date:
            candidates.append(self.discovery_date)
        if candidates:
            return min(candidates)

    @property
    def last_date(self):
        """
        last day in the project lifetime. it's the greater of
        the project end date and default end date.
        """
        candidates = []
        try:
            candidates.append(self.default_end_date)
        except ValueError:
            pass
        if self.end_date:
            candidates.append(self.end_date)
        if candidates:
            return max(candidates)

    @property
    def first_task(self):
        return self.tasks.order_by('start_date').first()

    @property
    def last_task(self):
        return self.tasks.order_by('-end_date').first()

    @property
    def first_budget(self):
        return self.budgets.order_by('start_date').first()

    @property
    def last_budget(self):
        return self.budgets.order_by('-start_date').first()

    @property
    def first_cost(self):
        return self.costs.order_by('start_date').first()

    @property
    def last_cost(self):
        # end_date is optional
        by_end_date = self.costs.exclude(
            end_date__isnull=True).order_by('-end_date').first()
        by_start_date = self.costs.order_by('-start_date').first()
        if by_end_date and by_end_date.end_date > by_start_date.start_date:
            return by_end_date
        return by_start_date

    def spendings_between(self, start_date, end_date):
        contractor_cost = self.people_costs(
            start_date, end_date, contractor_only=True)
        non_contractor_cost = self.people_costs(
            start_date, end_date, non_contractor_only=True)
        additional_costs = self.additional_costs(start_date, end_date)
        value = {
            'contractor': contractor_cost,
            'non-contractor': non_contractor_cost,
            'additional': additional_costs,
            'budget': self.budget(start_date),
        }
        return value

    @property
    def default_start_date(self):
        """
        default start date is the date when the first spend occurs or
        the first budget allocated to the project.
        it is the smallest of these three start dates:
        first task, first budget, first cost.
        :return: a date object
        :raises: ValueError when none of the three dates
        are present.
        """
        candidates = []
        if self.first_task:
            candidates.append(self.first_task.start_date)
        if self.first_budget:
            candidates.append(self.first_budget.start_date)
        if self.first_cost:
            candidates.append(self.first_cost.start_date)
        return min(candidates)

    @property
    def default_end_date(self):
        """
        default end date is the date when the last spend occurs or
        the last budget allocated to the project.
        it is the smallest of these dates in the project:
        end date of the last task, start date of the last budget,
        the start date and end date of the last cost.
        :return: a date object
        :raises: ValueError when none of the three dates
        are present.
        """
        candidates = []
        if self.last_task:
            candidates.append(self.last_task.end_date)
        if self.last_budget:
            candidates.append(self.last_budget.start_date)
        if self.last_cost:
            if self.last_cost.end_date:
                candidates.append(self.last_cost.end_date)
            else:
                candidates.append(self.last_cost.start_date)
        return max(candidates)

    def profile(self, start_date=None, end_date=None, freq=None):
        """
        get the profile of a project in a time window.
        :param project_ids: a list of project_ids, if the value is not
        specified, get all projects.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary representing the profile
        """
        rag = self.rag()
        rag = rag.get_rag_display() if rag else ''
        if self.client:
            service_area = {
                'id': self.client.id,
                'name': self.client.name,
            }
        else:
            service_area = {}
        result = {
            'id': self.id,
            'name': self.name,
            'service_area': service_area,
            'description': self.description,
            'discovery_date': self.discovery_date,
            'alpha_date': self.alpha_date,
            'beta_date': self.beta_date,
            'live_date': self.live_date,
            'end_date': self.end_date,
            'first_date': self.first_date,
            'last_date': self.last_date,
            'rag': rag,
            'budget': self.budget(),
            'team_size': self.team_size(start_date, end_date),
            'cost_to_date': self.cost_to_date,
            'financial': {},
        }
        if not start_date:
            try:
                start_date = self.default_start_date
            except ValueError:
                return result
        if not end_date:
            try:
                end_date = self.default_end_date
            except ValueError:
                return result
        if freq:
            time_windows = slice_time_window(start_date, end_date, freq)
        else:
            time_windows = [(start_date, end_date)]
        for sdate, edate in time_windows:
            # use '{sdate}~{edate}' as the dictionary key.
            # this is perhaps not the best way to do it.
            # leave it open to change when a better way emerges.
            key = '{}~{}'.format(sdate.strftime('%Y-%m-%d'),
                                 edate.strftime('%Y-%m-%d'))
            result['financial'][key] = self.spendings_between(sdate, edate)
        return result

    def __str__(self):
        return self.name

    @method_cache(timeout=24 * 60 * 60)
    def people_costs(self, start_date, end_date, contractor_only=False,
                     non_contractor_only=False):
        """
        get money spent in a time window
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param contractor_only: True to return only money spent on contractors
        :param non_contractor_only: True to return only money spent on
        non-contractors
        :return: a decimal for total spending
        """
        if contractor_only and non_contractor_only:
            raise ValueError('only one of contractor_only and'
                             ' non_contractor_only can be true')
        if contractor_only:
            tasks = self.tasks.filter(person__is_contractor=True)
        elif non_contractor_only:
            tasks = self.tasks.filter(person__is_contractor=False)
        else:
            tasks = self.tasks.all()
        spending_per_task = [task.people_costs(start_date, end_date)
                             for task in tasks]
        return sum(spending_per_task)

    def additional_costs(self, start_date, end_date):
        def cost_of_cost(cost):
            return cost.cost_between(start_date, end_date)

        return sum(map(cost_of_cost, self.costs.filter(
            Q(end_date__gte=start_date) | Q(end_date__isnull=True),
            start_date__lte=end_date
        ))) or Decimal('0')

    @property
    def cost_to_date(self):
        """
        cost of the project from the start to today
        """
        try:
            spendings = self.spendings_between(
                self.default_start_date, date.today())
        except ValueError:
            return 0
        return sum(spendings[item] for item in
                   ['contractor', 'non-contractor', 'additional'])

    @property
    def total_cost(self):
        """
        cost of the project from the beginning to the end
        """
        try:
            spendings = self.spendings_between(
                self.default_start_date,
                self.default_end_date)
        except ValueError:
            return 0
        return sum(spendings[item] for item in
                   ['contractor', 'non-contractor', 'additional'])

    def budget(self, on=None):
        """
        get the budget for the project on a date
        :param on: optional date object. if empty use today's date
        :return: a decimal for the budget
        """
        if not on:
            on = date.today()
        budget = self.budgets.filter(start_date__lte=on)\
            .order_by('-start_date').first()
        return budget.budget if budget else Decimal('0')

    def rag(self, on=None):
        """
        get the rag for the project on a date
        :param on: optional date object. if empty use today's date
        :return: a rag object
        """
        if not on:
            on = date.today()
        rag = self.rags.filter(start_date__lte=on)\
            .order_by('-start_date').first()
        return rag

    def time_spent(self, start_date=None, end_date=None):
        """
        get the days spent on the project during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :return: number of days, a decimal
        """
        try:
            if not start_date:
                start_date = self.first_task.start_date
            if not end_date:
                end_date = self.last_task.end_date
        except AttributeError:  # when there is no task in a project
            return 0

        return sum(task.time_spent(start_date, end_date)
                   for task in self.tasks.all())

    def team_size(self, start_date=None, end_date=None):
        """
        team size measures the number of people working on the project.
        it is the total man-days / num of workday from a start date to
        an end date.
        :param start_date: date object for the start date.
        if not specified, use the date 8 days ago from today.
        :param end_date: date object for the end date.
        if not specified, use the date of yesterday.
        """
        if not end_date:
            end_date = date.today() - timedelta(days=1)
        if not start_date:
            start_date = end_date - timedelta(days=7)
        workdays = get_workdays(start_date, end_date)
        if workdays == 0:  # avoid zero division
            return 0
        return self.time_spent(start_date, end_date) / workdays

    class Meta:
        permissions = (
            ('upload_project', 'Can upload monthly payroll'),
        )


class Cost(models.Model):
    project = models.ForeignKey('Project', related_name='costs')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=128, null=True)
    note = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.PositiveSmallIntegerField(
        choices=COST_TYPES, default=COST_TYPES.ONE_OFF)

    def cost_between(self, start_date, end_date):
        start_date = max(start_date, self.start_date)
        end_date = min(end_date, self.end_date or end_date)
        if self.type == COST_TYPES.ONE_OFF:
            if start_date <= self.start_date <= end_date:
                return self.cost
            return Decimal('0')

        dates = dates_between(start_date, end_date, self.freq,
                              bymonthday=self.bymonthday,
                              byyearday=self.byyearday)
        # print(self, start_date, end_date, dates)
        return len(dates) * self.cost

    @property
    def byyearday(self):
        if self.type == COST_TYPES.ANNUALLY:
            return self.start_date.timetuple().tm_yday

    @property
    def bymonthday(self):
        if self.type == COST_TYPES.MONTHLY:
            return self.start_date.day

    @property
    def freq(self):
        if self.type == COST_TYPES.MONTHLY:
            return MONTHLY
        elif self.type == COST_TYPES.ANNUALLY:
            return YEARLY


class Budget(models.Model):
    project = models.ForeignKey('Project', related_name='budgets')
    start_date = models.DateField()
    budget = models.DecimalField(max_digits=16, decimal_places=2)


class RAG(models.Model):
    project = models.ForeignKey('Project', related_name='rags')
    start_date = models.DateField()
    rag = models.PositiveSmallIntegerField(
        choices=RAG_TYPES, default=RAG_TYPES.GREEN)


class Note(models.Model):
    project = models.ForeignKey('Project', related_name='notes')
    date = models.DateField()
    name = models.CharField(max_length=128, null=True)
    note = models.TextField(null=True, blank=True)


class TaskManager(models.Manager):

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
    project = models.ForeignKey('Project', related_name='tasks')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=10, decimal_places=5)
    float_id = models.CharField(max_length=128, unique=True)
    raw_data = JSONField(null=True)
    objects = TaskManager()

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

    def people_costs(self, start_date=None, end_date=None):
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
