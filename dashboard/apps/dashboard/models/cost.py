# -*- coding: utf-8 -*-
from decimal import Decimal
from datetime import date

from django.db.models import Q
from django.db import models
from django.utils.translation import ugettext_lazy
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, YEARLY, DAILY

from ..constants import COST_TYPES
from dashboard.libs.rate_converter import RATE_TYPES
from dashboard.libs.date_tools import (
    get_overlap, dates_between)
from dashboard.libs.rate_converter import RateConverter, dec_workdays


class AditionalCostsMixin():
    def get_costs_between(self, start_date, end_date, name=None,
                          attribute='costs', types=[]):
        costs = getattr(self, attribute).all()
        if start_date and end_date:
            costs = costs.filter(
                Q(end_date__gte=start_date) | Q(end_date__isnull=True),
                start_date__lte=end_date
            )

        if name and isinstance(name, str):
            costs = costs.filter(name=name)

        if types:
            costs = costs.filter(type__in=types)

        return costs

    def additional_costs(self, start_date, end_date, name=None,
                         attribute='costs', types=[]):
        def cost_of_cost(cost):
            return cost.cost_between(start_date, end_date)

        costs = self.get_costs_between(start_date, end_date, name=name,
                                       attribute=attribute, types=types)

        return sum(map(cost_of_cost, costs)) or Decimal('0')


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

        return self.cost / cost_working_days * \
            overlap_working_days / dec_workdays(start_date, end_date)

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
        return DAILY

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
        ordering = ['start_date', 'id']


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
        ordering = ('-start_date', '-id')
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
