# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy

from dashboard.libs.rate_converter import (
    RATE_TYPES, dec_workdays, average_rate_from_segments, last_date_in_month)
from .cost import AditionalCostsMixin
from ..constants import COST_TYPES


class Person(models.Model, AditionalCostsMixin):
    float_id = models.CharField(max_length=128, unique=True)
    staff_number = models.PositiveIntegerField(null=True, blank=True, unique=True)
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

    @property
    def type(self):
        if self.is_contractor:
            return 'Contractor'
        else:
            return 'Civil Servant'

    @property
    def rate_type(self):
        rate = self.rates.on(on=date.today())
        if rate:
            return RATE_TYPES.for_value(rate.rate_type).display

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = ugettext_lazy('People')
        permissions = (
            ('upload_person', 'Can upload monthly payroll'),
            ('export_person_rates', 'Can export person rates'),
        )

    def additional_rate(self, start_date, end_date, name=None,
                        predict_based_on=None):
        costs = self.get_costs_between(start_date, end_date, name=name)
        if not self.is_contractor and not costs:
            # If additional costs haven't been added for the month then
            # estimate of last set of additional costs
            if predict_based_on:
                rate = self.rates.on(on=predict_based_on)
            else:
                rate = self.rates.on(on=date.today())
            if rate:
                start_date = rate.start_date
                end_date = last_date_in_month(rate.start_date)
                costs = self.get_costs_between(
                    rate.start_date,
                    end_date,
                    name=name,
                    types=[COST_TYPES.MONTHLY])

        if not costs:
            return Decimal('0')

        last_cost = costs.order_by('-end_date')[0]
        if last_cost.end_date:
            if last_cost.end_date <= end_date:
                end_date = last_cost.end_date
            if last_cost.end_date <= start_date:
                start_date = last_cost.start_date
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
            start = max(rate.start_date, start_date)
            try:
                end = rate_list[n + 1].start_date - timedelta(days=1)
            except IndexError:
                end = end_date
            segments.append(
                (start, end, rate.rate_between(start, end))
            )

        total_workdays = dec_workdays(start_date, end_date)
        average_rate = average_rate_from_segments(segments, total_workdays)
        return average_rate or Decimal('0')

    def rate_between(self, start_date, end_date):
        """
        average day with aditional costs day rate rate in range
        param: start_date: date object - beginning of time period for average
        param: end_date: date object - end of time period for average
        return: Decimal object - average day rate
        """
        average_rate = self.base_rate_between(start_date, end_date)

        if not average_rate:
            return Decimal('0')

        return average_rate + self.additional_rate(start_date, end_date)

    def base_rate_on(self, on):
        """
        base rate at time of date
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - rate on date
        """
        rate = self.rates.on(on=on)

        if not rate:
            return Decimal('0')

        return rate.rate_on(on)

    def rate_on(self, on):
        """
        rate at time of date
        param: on: date object - if no start or end then rate on specific date
        return: Decimal object - rate on date
        """
        base_rate = self.base_rate_on(on)

        if not base_rate:
            return Decimal('0')

        return base_rate + self.additional_rate(on, on)
