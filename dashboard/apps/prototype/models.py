# -*- coding: utf-8 -*-
from datetime import timedelta, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, YEARLY
from urllib.parse import urlparse

from django.db import models
from django.core import urlresolvers
from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import ugettext_lazy

from dashboard.libs.date_tools import (
    get_workdays, get_overlap, slice_time_window, dates_between)
from dashboard.libs.rate_converter import RATE_TYPES, RateConverter, \
    dec_workdays, average_rate_from_segments
from dashboard.libs.cache_tools import method_cache

from .constants import RAG_TYPES, COST_TYPES, STATUS_TYPES


class BaseCost(models.Model):
    type = models.PositiveSmallIntegerField(
        choices=COST_TYPES, default=COST_TYPES.ONE_OFF)
    name = models.CharField(max_length=128, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=ugettext_lazy('Amount'))
    note = models.TextField(null=True, blank=True)

    def cost_between(self, start_date, end_date):
        start_date = max(start_date, self.start_date) if start_date else \
            self.start_date
        end_date = min(end_date, self.end_date or end_date) if end_date else \
            self.end_date
        # If there is no end date then set it for today
        end_date = end_date or date.today()
        if self.type == COST_TYPES.ONE_OFF:
            if start_date <= self.start_date <= end_date:
                return self.cost
            return Decimal('0')

        dates = dates_between(start_date, end_date, self.freq,
                              bymonthday=self.bymonthday,
                              byyearday=self.byyearday)

        return len(dates) * self.cost

    def rate_between(self, start_date, end_date):
        if not self.end_date:
            if self.type == COST_TYPES.MONTHLY:
                cost_end_date = self.start_date + relativedelta(months=1)
            elif self.type == COST_TYPES.ANNUALLY:
                cost_end_date = self.start_date + relativedelta(years=1)
            else:
                raise Exception('Cant get rate on one off cost')
        else:
            cost_end_date = self.end_date

        cost_working_days = dec_workdays(self.start_date, cost_end_date)

        overlap = get_overlap(
            (self.start_date, cost_end_date),
            (start_date, end_date))

        if not overlap:
            return Decimal('0')

        overlap_working_days = dec_workdays(*overlap)

        return self.cost * overlap_working_days / cost_working_days

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

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'note': self.note,
            'cost': self.cost,
            'product_id': self.product_id,
            'freq': dict(COST_TYPES.choices)[self.type]
        }

    class Meta:
        abstract = True
        ordering = ['start_date']


class AditionalCostsMixin():
    def get_costs_between(self, start_date, end_date, name=None,
                          attribute='costs'):
        costs = getattr(self, attribute).all()
        if start_date and end_date:
            costs = costs.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                start_date__lte=end_date
            )

        if name:
            costs = costs.filter(name=name)

        return costs

    def additional_costs(self, start_date, end_date, name=None,
                         attribute='costs'):
        def cost_of_cost(cost):
            return cost.cost_between(start_date, end_date)

        costs = self.get_costs_between(start_date, end_date, name=None,
                                       attribute=attribute)

        return sum(map(cost_of_cost, costs)) or Decimal('0')


class Person(models.Model, AditionalCostsMixin):
    float_id = models.CharField(max_length=128, unique=True)
    staff_number = models.PositiveIntegerField(null=True, unique=True)
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

    def additional_rate(self, start_date, end_date, name=None):
        costs = self.get_costs_between(start_date, end_date, name=name)

        if not costs:
            return Decimal('0')

        return sum([c.rate_between(start_date, end_date) for c in costs])

    def base_rate_between(self, start_date, end_date):
        """
        average base day rate in range
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

        average_rate = average_rate_from_segments(segments, total_workdays)

        return average_rate

    def rate_between(self, start_date, end_date):
        """
        average day with aditional costs day rate rate in range
        param: start_date: date object - beginning of time period for average
        param: end_date: date object - end of time period for average
        return: Decimal object - average day rate
        """
        average_rate = self.base_rate_between(start_date, end_date)

        if average_rate:
            return average_rate + self.additional_rate(start_date, end_date)

    def rate_on(self, on):
        """
        rate at time of date
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - rate on date
        """
        rate = self.rates.on(on=on)
        if rate:
            return rate.rate_on(on) + self.additional_rate(on, on)


class PersonCost(BaseCost):
    person = models.ForeignKey('Person', related_name='costs')


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


class Area(models.Model):
    name = models.CharField(max_length=128)
    float_id = models.CharField(max_length=128, unique=True)
    visible = models.BooleanField(default=True)
    manager = models.ForeignKey(
        'Person', related_name='+', verbose_name='service manager', null=True)
    raw_data = JSONField(null=True)

    class Meta:
        verbose_name = ugettext_lazy('service area')

    def __str__(self):
        return self.name

    def profile(self, product_ids=None, start_date=None, end_date=None,
                freq=None):
        """
        get the profile of a service area in a time window.
        :param product_ids: a list of product_ids, if the value is not
        specified, get all products.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary representing the profile
        """
        product_ids_in_a_group = [
            p.id
            for group in ProductGroup.objects.all()
            for p in group.products.all()
        ]
        products = self.products.visible().exclude(
            id__in=product_ids_in_a_group)
        product_groups = [group for group in ProductGroup.objects.all()
                          if group.area and group.area.id == self.id]
        if product_ids is not None:
            products = products.filter(id__in=product_ids)
        result = {
            'id': self.id,
            'name': self.name
        }
        result['products'] = {
            'product:{}'.format(product.id): product.profile(
                start_date, end_date, freq)
            for product in products
        }
        result['products'].update({
            'product-group:{}'.format(group.id): group.profile(
                start_date, end_date, freq)
            for group in product_groups
        })
        return result


class ProductManager(models.Manager):
    use_for_related_fields = True

    def visible(self):
        return self.get_queryset().filter(visible=True).filter(
            models.Q(area=None) | models.Q(area__visible=True)
        )


class BaseProduct(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    product_manager = models.ForeignKey('Person', related_name='+', null=True)
    delivery_manager = models.ForeignKey('Person', related_name='+', null=True)
    discovery_date = models.DateField(null=True, blank=True,
                                      verbose_name='discovery start')
    alpha_date = models.DateField(null=True, blank=True,
                                  verbose_name='alpha start')
    beta_date = models.DateField(null=True, blank=True,
                                 verbose_name='beta start')
    live_date = models.DateField(null=True, blank=True,
                                 verbose_name='live start')
    end_date = models.DateField(null=True, blank=True)

    @property
    def admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        name = 'admin:{}_{}_change'.format(content_type.app_label,
                                           content_type.model)
        try:
            return urlresolvers.reverse(name, args=(self.id,))
        except urlresolvers.NoReverseMatch:
            # in case not exposed on admin site
            return ''

    def __str__(self):
        return self.name

    @property
    def phase(self):
        today = date.today()
        if self.end_date and today >= self.end_date:
            return 'Ended'
        elif self.live_date and today >= self.live_date:
            return 'Live'
        elif self.beta_date and today >= self.beta_date:
            return 'Beta'
        elif self.alpha_date and today >= self.alpha_date:
            return 'Alpha'
        elif self.discovery_date and today >= self.discovery_date:
            return 'Discovery'
        else:
            return 'Not Defined'

    @property
    def financial_rag(self):
        """
        financial rag is one of 'RED', 'AMBER' and 'GREEN'.
        A measure of how well the product is keeping to budget.
        RED: total_cost >= 110% * budget
        AMBER: budget < total_cost < 110% * budget
        GREEN: total_cost <= budget
        """
        budget = self.final_budget
        total_cost = self.total_cost
        if budget >= total_cost:
            return RAG_TYPES.GREEN.constant
        if budget * Decimal('1.1') >= total_cost:
            return RAG_TYPES.AMBER.constant
        return RAG_TYPES.RED.constant

    def status(self, on=None):
        """
        get the status for the product group on a date
        :param on: optional date object. if empty use today's date
        :return: a rag object
        """
        if not on:
            on = date.today()
        status = self.statuses.filter(
            start_date__lte=on).order_by('-start_date').first()
        return status

    def stats_on(self, on):
        """
        key statistics snapshot on a given date
        :param on: date when the snapsot is taken
        """
        try:
            return self.stats_between(
                self.first_date, on - timedelta(days=1))
        except ValueError:  # when no first_date
            return {
                'contractor': Decimal('0'),
                'non-contractor': Decimal('0'),
                'additional': Decimal('0'),
                'budget': Decimal('0'),
                'savings': Decimal('0'),
                'total': Decimal('0'),
                'remaining': Decimal('0')
            }

    def stats_between(self, start_date, end_date):
        """
        key statistics in a time window
        :param start_date: start date of time window, a date object
        :param end_date: start date of time window, a date object
        :return a dictionary
        """
        contractor_cost = self.people_costs(
            start_date, end_date, contractor_only=True)
        non_contractor_cost = self.people_costs(
            start_date, end_date, non_contractor_only=True)
        additional_costs = self.additional_costs(start_date, end_date)
        total = contractor_cost + non_contractor_cost + additional_costs
        # technically the budget is for 23:59:59 of end_date,
        # which rounded to next day at 00:00:00
        budget = self.budget(end_date + timedelta(days=1))
        remaining = budget - total
        savings = self.savings_between(start_date, end_date)
        stats = {
            'contractor': contractor_cost,
            'non-contractor': non_contractor_cost,
            'additional': additional_costs,
            'budget': budget,
            'savings': savings,
            'total': total,
            'remaining': remaining
        }
        return stats

    def key_dates(self, freq=None):
        """
        key dates of the product. these include the start of
        phases, today. if a frequency is specified, it also include
        start of time frames and end of last time frame sliced by frequency.
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary
        """
        phase_start_dates = {
            '{}-{}'.format('-'.join(name.split(' ')),
                           date.strftime('%Y%m%d')): {
               'name': name,
               'date': date,
               'type': 'phase start',
            }
            for (name, date) in [
                ('discovery start', self.discovery_date),
                ('alpha start', self.alpha_date),
                ('beta start', self.beta_date),
                ('live start', self.live_date),
                ('today', date.today()),
                # by convention, when we say the product ends on '31 Aug 16',
                # what we really mean is it ends on 'end of 31 Aug 16', i.e.
                # 31/08/16 23:59:59, which is essentially beginning of
                # '1 Sept 16'.
                ('end of day on end date', self.end_date + timedelta(days=1)
                 if self.end_date else None)
            ]
            if date
        }
        budget_start_dates = {
            'new-budget-{}'.format(bgt.start_date.strftime('%Y%m%d')): {
                'name': 'new budget {}'.format(bgt.budget),
                'date': bgt.start_date,
                'type': 'new budget set'
            }
            for bgt in self.budgets.all()
        }

        if not freq:
            return {**phase_start_dates, **budget_start_dates}

        try:
            time_windows = slice_time_window(
                self.first_date,
                self.last_date,
                freq, extend=True)
        except ValueError:  # when no first_date
            return {**phase_start_dates, **budget_start_dates}

        def _key(sdate, edate):
            return 'start-of-{}-{}'.format(
                sdate.strftime('%Y%m%d'), edate.strftime('%Y%m%d'))
        time_window_start_dates = {
            _key(sdate, edate): {
                'name': _key(sdate, edate),
                'date': sdate,
                'type': 'start of a time window'
            }
            for sdate, edate in time_windows
        }
        rear_time_window = time_windows[-1]
        key = 'first-day-after-rear-time-window-{}-{}'.format(
            *rear_time_window)
        day_after_time_windows = {
            key: {
                'name': key,
                'date': rear_time_window[1] + timedelta(days=1),
                'type': 'first day after rear time window'
            }
        }
        return {
            **phase_start_dates,
            **budget_start_dates,
            **time_window_start_dates,
            **day_after_time_windows
        }

    def stats_on_key_dates(self, freq=None):
        """
        statistics on key dates
        return: a dictionary
        """
        return {
            k: {**{'stats': self.stats_on(v['date'])}, **v}
            for k, v in self.key_dates(freq).items()
        }

    def stats_in_time_frames(self, start_date, end_date, freq):
        """
        cumulative stats of time frames sliced by freq
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary
        """
        if not start_date:
            try:
                start_date = self.first_date
            except ValueError:
                return {}
        if not end_date:
            try:
                end_date = self.last_date
            except ValueError:
                return {}
        if freq:
            time_windows = slice_time_window(
                start_date, end_date, freq, extend=True)
        else:
            time_windows = [(start_date, end_date)]
        result = {}
        for sdate, edate in time_windows:
            # use '{sdate}~{edate}' as the dictionary key.
            # this is perhaps not the best way to do it.
            # leave it open to change when a better way emerges.
            key = '{}~{}'.format(sdate.strftime('%Y-%m-%d'),
                                 edate.strftime('%Y-%m-%d'))
            result[key] = self.stats_between(sdate, edate)
        return result

    @property
    def managers(self):
        """
        get the product manager, delivery manager and service manager
        of the product
        :return: a dictionary
        """
        result = {}
        if self.product_manager:
            result['product_manager'] = self.product_manager.name
        if self.delivery_manager:
            result['delivery_manager'] = self.delivery_manager.name
        if self.area and self.area.manager:
            result['service_manager'] = self.area.manager.name
        return result

    def profile(self, start_date=None, end_date=None, freq=None):
        """
        get the profile of a product group in a time window.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :return: a dictionary representing the profile
        """
        status = self.status()
        status = status.as_dict() if status else {}
        if self.area:
            service_area = {
                'id': self.area.id,
                'name': self.area.name,
            }
        else:
            service_area = {}
        try:
            first_date = self.first_date
        except ValueError:
            first_date = None
        try:
            last_date = self.last_date
        except ValueError:
            last_date = None
        result = {
            'id': self.id,
            'name': self.name,
            'status': status,
            'type': self.__class__.__name__,
            'service_area': service_area,
            'description': self.description,
            'managers': self.managers,
            'discovery_date': self.discovery_date,
            'alpha_date': self.alpha_date,
            'beta_date': self.beta_date,
            'live_date': self.live_date,
            'end_date': self.end_date,
            'first_date': first_date,
            'last_date': last_date,
            'financial': {
                'time_frames': self.stats_in_time_frames(
                    start_date, end_date, freq),
                'key_dates': self.stats_on_key_dates(freq)
            },
            'financial_rag': self.financial_rag,
            'budget': self.budget(),
            'current_fte': self.current_fte(start_date, end_date),
            'cost_to_date': self.cost_to_date,
            'phase': self.phase,
            'costs': {c.id: c.as_dict() for c in self.costs.all()},
            'savings': {s.id: s.as_dict() for s in self.savings.all()},
            'links': [l.as_dict() for l in self.links.all()]
        }
        return result

    def can_user_change(self, user):
        ctype = ContentType.objects.get_for_model(self.__class__)
        perm = '{}.change_{}'.format(ctype.app_label, ctype.model)
        return user.has_perm(perm)

    class Meta:
        abstract = True


class Product(BaseProduct, AditionalCostsMixin):
    hr_id = models.CharField(max_length=12, unique=True, null=True)
    float_id = models.CharField(max_length=128, unique=True)
    is_billable = models.BooleanField(default=True)
    area = models.ForeignKey('Area', related_name='products',
                             verbose_name='service area', null=True)
    visible = models.BooleanField(default=True)
    raw_data = JSONField(null=True)

    objects = ProductManager()

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

    @property
    def first_date(self):
        """
        default start date is the date when the first spend occurs or the
        first budget allocated to the product or the specified discovery date
        it is the smallest of these four start dates:
        first task, first budget, first cost, discovery date
        :return: a date object
        :raises: ValueError when none of the dates are present.
        """
        candidates = []
        if self.first_task:
            candidates.append(self.first_task.start_date)
        if self.first_budget:
            candidates.append(self.first_budget.start_date)
        if self.first_cost:
            candidates.append(self.first_cost.start_date)
        if self.discovery_date:
            candidates.append(self.discovery_date)
        return min(candidates)

    @property
    def last_date(self):
        """
        default end date is the date when the last spend occurs or
        the last budget allocated to the product or the specified end date
        it is the greatest of these dates in the product:
        end date of the last task, start date of the last budget,
        the start date and end date of the last cost, end date of the product
        :return: a date object
        :raises: ValueError when none of the dates are present.
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
        if self.end_date:
            candidates.append(self.end_date)
        return max(candidates)

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

        tasks = self.tasks.between(start_date, end_date)
        if contractor_only:
            tasks = tasks.filter(person__is_contractor=True)
        elif non_contractor_only:
            tasks = tasks.filter(person__is_contractor=False)

        spending_per_task = [task.people_costs(start_date, end_date)
                             for task in tasks]
        return sum(spending_per_task)

    def people_additional_costs(self, start_date, end_date, name=None):
        """
        get the additional non salary people costs for a product
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param name: only get the additional people costs of this name
        :return: a decimal for total spending
        """
        tasks = self.tasks.between(start_date, end_date)
        additinal_task_costs = [task.people_costs(start_date, end_date, name)
                                for task in tasks]
        return sum(additinal_task_costs)

    @property
    def cost_to_date(self):
        """
        cost of the product from the start to today
        """
        stats = self.stats_on(date.today())
        return sum(stats[item] for item in
                   ['contractor', 'non-contractor', 'additional'])

    @property
    def total_cost(self):
        """
        cost of the product from the beginning to the end of the end date
        """
        try:
            stats = self.stats_on(self.last_date + timedelta(days=1))
        except ValueError:  # when no last_date
            return Decimal('0')
        return sum(stats[item] for item in
                   ['contractor', 'non-contractor', 'additional'])

    def budget(self, on=None):
        """
        get the budget for the product on a date
        :param on: optional date object. if empty use today's date
        :return: a decimal for the budget
        """
        if not on:
            on = date.today()
        budget = self.budgets.filter(start_date__lte=on)\
            .order_by('-start_date').first()
        return budget.budget if budget else Decimal('0')

    @property
    def final_budget(self):
        """
        budget on the default end date
        """
        try:
            return self.budget(on=self.last_date)
        except ValueError:
            return Decimal('0')

    def time_spent(self, start_date=None, end_date=None):
        """
        get the days spent on the product during a time window.
        :param start_date: start date of the time window, a date object
        :param end_date: end date of the time window, a date object
        :return: number of days, a decimal
        """
        try:
            if not start_date:
                start_date = self.first_task.start_date
            if not end_date:
                end_date = self.last_task.end_date
        except AttributeError:  # when there is no task in a product
            return Decimal('0')

        return sum(task.time_spent(start_date, end_date)
                   for task in self.tasks.all())

    def current_fte(self, start_date=None, end_date=None):
        """
        current FTE measures the number of people working on the product.
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
            return Decimal('0')
        return self.time_spent(start_date, end_date) / workdays

    def savings_between(self, start_date=None, end_date=None):
        """
        returns total savings for the product

        :param start_date: date object for the start date.
        if not specified, use the date of the first saving for the product.
        :param end_date: date object for the end date.
        if not specified, use the date of today.
        """
        return self.additional_costs(start_date, end_date,
                                     attribute='savings')

    class Meta:
        permissions = (
            ('adjustmentexport_product', 'Can run Adjustment Export'),
            ('intercompanyexport_product', 'Can run Intercompany Export'),
            ('productdetailexport_product', 'Can run Intercompany Export'),
        )
        verbose_name = ugettext_lazy('product')


class Cost(BaseCost):
    product = models.ForeignKey('Product', related_name='costs')


class Saving(BaseCost):
    product = models.ForeignKey('Product', related_name='savings')


class Budget(models.Model):
    product = models.ForeignKey('Product', related_name='budgets')
    start_date = models.DateField()
    budget = models.DecimalField(
        max_digits=16, decimal_places=2,
        help_text=ugettext_lazy('Please enter the total budget'))
    note = models.TextField(null=True, blank=True)


class Status(models.Model):
    start_date = models.DateField()
    status = models.PositiveSmallIntegerField(
        choices=STATUS_TYPES, default=STATUS_TYPES.OK)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.get_status_display())

    def as_dict(self):
        return {
            'status': self.get_status_display(),
            'reason': self.reason,
            'start_date': self.start_date
        }

    class Meta:
        abstract = True
        verbose_name_plural = "statuses"


class ProductStatus(Status):
    product = models.ForeignKey('Product', related_name='statuses')


class ProductGroupStatus(Status):
    product_group = models.ForeignKey('ProductGroup', related_name='statuses')


class ProductGroup(BaseProduct):
    products = models.ManyToManyField(
        Product,
        related_name='product_groups',
        limit_choices_to=lambda: {'id__in': Product.objects.visible()})

    @property
    def budgets(self):
        return Budget.objects.filter(
            product_id__in=[p.id for p in self.products.all()])

    @property
    def savings(self):
        return Saving.objects.filter(
            product_id__in=[p.id for p in self.products.all()])

    @property
    def first_date(self):
        return min([p.first_date for p in self.products.all()])

    @property
    def last_date(self):
        return max([p.last_date for p in self.products.all()])

    def budget(self, on=None):
        return sum([p.budget(on) for p in self.products.all()])

    @property
    def costs(self):
        return Cost.objects.filter(
            product_id__in=[p.id for p in self.products.all()])

    @property
    def cost_to_date(self):
        return sum([p.cost_to_date for p in self.products.all()])

    @property
    def total_cost(self):
        return sum([p.total_cost for p in self.products.all()])

    @property
    def area(self):
        areas = [p.area for p in self.products.all() if p.area]
        if len({c.id for c in areas}) == 1:
            return areas[0]

    @property
    def links(self):
        return Link.objects.filter(
            product_id__in=[p.id for p in self.products.visible()])

    @property
    def final_budget(self):
        return sum(p.final_budget for p in self.products.all())

    def current_fte(self, start_date=None, end_date=None):
        """
        current FTE measures the number of people working on the product.
        it is the total man-days / num of workday from a start date to
        an end date.
        :param start_date: date object for the start date.
        if not specified, use the date 8 days ago from today.
        :param end_date: date object for the end date.
        if not specified, use the date of yesterday.
        """
        return sum(p.current_fte(start_date, end_date)
                   for p in self.products.all())

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
        return sum(p.people_costs(start_date, end_date, contractor_only,
                                  non_contractor_only)
                   for p in self.products.filter(visible=True))

    def additional_costs(self, start_date, end_date):
        return sum(p.additional_costs(start_date, end_date) for p in
                   self.products.filter(visible=True))

    def savings_between(self, start_date=None, end_date=None):
        """
        returns total savings for the product

        :param start_date: date object for the start date.
        if not specified, use the date of the first saving for the product.
        :param end_date: date object for the end date.
        if not specified, use the date of today.
        """
        return sum(p.savings_between(start_date, end_date) for p in
                   self.products.filter(visible=True))


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


class Link(models.Model):
    product = models.ForeignKey('Product', related_name='links')
    name = models.CharField(max_length=150, null=True, blank=True)
    url = models.URLField()
    note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['url']

    def __str__(self):
        return self.name

    @property
    def type(self):
        hostname = urlparse(self.url).hostname
        return hostname.replace('.', '-')

    def as_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'note': self.note,
            'type': self.type,
        }
