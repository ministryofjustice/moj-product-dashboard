# -*- coding: utf-8 -*-
from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy

from dashboard.libs.date_tools import (
    financial_year_tuple, slice_time_window, get_workdays)
from dashboard.libs.cache_tools import method_cache
from ..constants import RAG_TYPES, STATUS_TYPES, COST_TYPES
from .cost import Cost, AditionalCostsMixin, Budget, Saving
from .link import Link


class BaseProduct(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    product_manager = models.ForeignKey(
        'Person', related_name='+', null=True, blank=True)
    delivery_manager = models.ForeignKey(
        'Person', related_name='+', null=True, blank=True)
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

    def financial_rag(self, calculation_start_date=None):
        """
        financial rag is one of 'RED', 'AMBER' and 'GREEN'.
        A measure of how well the product is keeping to budget.
        RED: total_cost >= 110% * budget
        AMBER: budget < total_cost < 110% * budget
        GREEN: total_cost <= budget
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        """
        budget = self.final_budget
        total_cost = self.total_cost(
            calculation_start_date=calculation_start_date)
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
            start_date__lte=on).order_by('-start_date', '-id').first()
        return status

    def stats_on(self, on, calculation_start_date=None):
        """
        key statistics snapshot on a given date
        :param on: date when the snapsot is taken
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        """
        try:
            return self.stats_between(
                self.first_date, on - timedelta(days=1),
                calculation_start_date=calculation_start_date)
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

    def stats_between(self, start_date, end_date, calculation_start_date=None):
        """
        key statistics in a time window
        :param start_date: start date of time window, a date object
        :param end_date: start date of time window, a date object
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        :return a dictionary
        """
        contractor_cost = self.people_costs(
            start_date, end_date, contractor_only=True,
            calculation_start_date=calculation_start_date)
        non_contractor_cost = self.people_costs(
            start_date, end_date, non_contractor_only=True,
            calculation_start_date=calculation_start_date)
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

    def stats_on_key_dates(self, freq=None, calculation_start_date=None):
        """
        statistics on key dates
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        return: a dictionary
        """
        return {
            k: {**{'stats': self.stats_on(
                v['date'],
                calculation_start_date=calculation_start_date)}, **v}
            for k, v in self.key_dates(freq).items()
        }

    def stats_in_time_frames(self, start_date, end_date, freq,
                             calculation_start_date=None):
        """
        cumulative stats of time frames sliced by freq
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
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
            result[key] = self.stats_between(
                sdate, edate, calculation_start_date=calculation_start_date)
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

    def profile(self, start_date=None, end_date=None, freq='MS',
                calculation_start_date=None,
                ignore_cache=False):
        """
        get the profile of a product group in a time window.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        :return: a dictionary representing the profile
        """
        return self._profile(
            start_date, end_date, freq,
            calculation_start_date=calculation_start_date,
            ignore_cache=ignore_cache)

    @method_cache(timeout=24 * 60 * 60)
    def _profile(self, start_date, end_date, freq, calculation_start_date):
        """
        this method does not have default value for params
        hence more suitable for caching.
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
                    start_date, end_date, freq,
                    calculation_start_date=calculation_start_date),
                'key_dates': self.stats_on_key_dates(
                    freq, calculation_start_date)
            },
            'financial_rag': self.financial_rag(calculation_start_date),
            'budget': self.budget(),
            'current_fte': self.current_fte(start_date, end_date),
            'cost_to_date': self.cost_to_date(calculation_start_date=calculation_start_date),
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


class ProductManager(models.Manager):
    use_for_related_fields = True

    def visible(self):
        return self.get_queryset().filter(visible=True).filter(
            models.Q(area=None) | models.Q(area__visible=True)
        )


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
        last_non_repeating_task = self.tasks.filter(repeat_state=0).order_by(
            '-end_date').first()
        last_repeating_task = self.tasks.filter(repeat_state__gt=0).order_by(
            models.F('end_date') - models.F('start_date') + models.F('repeat_end')
        ).reverse().first()
        if (last_repeating_task and
                last_repeating_task.effective_end_date > last_non_repeating_task.end_date):
            return last_repeating_task
        else:
            return last_non_repeating_task

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
            candidates.append(self.last_task.effective_end_date)
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

    def people_costs(self, start_date, end_date, contractor_only=False,
                     non_contractor_only=False, calculation_start_date=None):
        """
        get money spent in a time window
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param contractor_only: True to return only money spent on contractors
        :param non_contractor_only: True to return only money spent on
        non-contractors
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
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

        spending_per_task = [
            task.people_costs(
                start_date,
                end_date,
                calculation_start_date=calculation_start_date
            )
            for task in tasks]
        return sum(spending_per_task)

    def people_additional_costs(self, start_date, end_date, name=True,
                                calculation_start_date=None):
        """
        get the additional non salary people costs for a product
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param name: only get the additional people costs of this name
        :param calculation_start_date: date when calculation for people costs
        :return: a decimal for total spending
        """
        tasks = self.tasks.between(start_date, end_date)
        additinal_task_costs = [
            task.people_costs(
                start_date,
                end_date,
                name,
                calculation_start_date=calculation_start_date
            )
            for task in tasks]
        return sum(additinal_task_costs)

    def non_contractor_salary_costs(self, start_date, end_date,
                                    calculation_start_date=None):
        aditional_costs = self.people_additional_costs(
            start_date, end_date,
            calculation_start_date=calculation_start_date)
        return self.people_costs(
            start_date, end_date, non_contractor_only=True,
            calculation_start_date=calculation_start_date) - aditional_costs

    def cost_to(self, d, calculation_start_date=None):
        """
        cost of the product from the start to date d
        """
        stats = self.stats_on(d, calculation_start_date=calculation_start_date)
        return sum(stats[item] for item in
                   ['contractor', 'non-contractor', 'additional'])

    def cost_to_date(self, calculation_start_date=None):
        """
        cost of the product from the start to today
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        :return: a decimal
        """
        return self.cost_to(
            date.today(), calculation_start_date=calculation_start_date)

    def total_cost(self, calculation_start_date=None):
        """
        cost of the product from the beginning to the end of the end date
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        """
        try:
            return self.cost_to(
                self.last_date + timedelta(days=1),
                calculation_start_date=calculation_start_date)
        except ValueError:  # when no last_date
            return Decimal('0')

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

    @property
    def discovery_fte(self):
        return self.current_fte(start_date=self.discovery_date,
                                end_date=self.alpha_date)

    @property
    def alpha_fte(self):
        return self.current_fte(start_date=self.alpha_date,
                                end_date=self.beta_date)

    @property
    def beta_fte(self):
        return self.current_fte(start_date=self.beta_date,
                                end_date=self.live_date)

    @property
    def live_fte(self):
        return self.current_fte(start_date=self.live_date,
                                end_date=self.end_date)

    @property
    def area_name(self):
        return self.area.name if self.area else ''

    def cost_of_stage(self, start, end, calculation_start_date=None):
        if start and end:
            return self.stats_between(
                start, end - timedelta(days=1), calculation_start_date)['total']

    def cost_of_discovery(self, calculation_start_date=None):
        return self.cost_of_stage(
            self.discovery_date, self.alpha_date,
            calculation_start_date=calculation_start_date)

    def cost_of_alpha(self, calculation_start_date=None):
        return self.cost_of_stage(
            self.alpha_date, self.beta_date,
            calculation_start_date=calculation_start_date)

    def cost_of_beta(self, calculation_start_date=None):
        return self.cost_of_stage(
            self.beta_date, self.live_date,
            calculation_start_date=calculation_start_date)

    def cost_in_fy(self, year, calculation_start_date=None):
        return self.stats_between(
            *financial_year_tuple(year),
            calculation_start_date=calculation_start_date)['total']

    def cost_of_sustaining(self, calculation_start_date=None):
        try:
            start, end = self.live_date, date.today()
            return self.people_costs(
                start, end, calculation_start_date=calculation_start_date) + \
                self.additional_costs(start, end, types=[COST_TYPES.ONE_OFF])
        except ValueError:
            pass

    @property
    def total_recurring_costs(self):
        try:
            return self.additional_costs(
                self.live_date, date.today(),
                types=[COST_TYPES.MONTHLY, COST_TYPES.ANNUALLY])
        except ValueError:
            pass

    @property
    def savings_enabled(self):
        try:
            return self.savings_between(self.first_date, date.today())
        except ValueError:
            pass

    class Meta:
        permissions = (
            ('adjustmentexport_product', 'Can run Adjustment Export'),
            ('intercompanyexport_product', 'Can run Intercompany Export'),
            ('productdetailexport_product', 'Can run Intercompany Export'),
        )
        verbose_name = ugettext_lazy('product')


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

    def cost_to_date(self, calculation_start_date=None):
        return sum([p.cost_to_date(calculation_start_date) for p in self.products.all()])

    def total_cost(self, calculation_start_date):
        return sum([p.total_cost(calculation_start_date) for p in self.products.all()])

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
                     non_contractor_only=False, calculation_start_date=None):
        """
        get money spent in a time window
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param contractor_only: True to return only money spent on contractors
        :param non_contractor_only: True to return only money spent on
        non-contractors
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        :return: a decimal for total spending
        """
        return sum(p.people_costs(start_date, end_date, contractor_only,
                                  non_contractor_only, calculation_start_date)
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
        ordering = ('-start_date', '-id')


class ProductStatus(Status):
    product = models.ForeignKey('Product', related_name='statuses')


class ProductGroupStatus(Status):
    product_group = models.ForeignKey('ProductGroup', related_name='statuses')
