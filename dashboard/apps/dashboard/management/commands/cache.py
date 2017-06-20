#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
command for generating and clearing cache
"""
import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings

from dashboard.apps.dashboard.models import Product
from dashboard.libs.date_tools import slice_time_window, financial_year_tuple
from .helpers import contains_any


def get_product_time_windows(product):
    """
    get all the key time windows for a product
    """
    # for most recent fte
    time_windows = [(None, None)]
    try:
        first_date = product.first_date
        last_date = product.last_date
    except ValueError:
        pass
    else:
        # every month from first date to last date if exists
        time_windows += slice_time_window(
            first_date,
            last_date,
            freq='MS',
            extend=True
        )
        # key dates
        time_windows += [
            (first_date, item['date'] - timedelta(days=1))
            for item in product.key_dates('MS').values()
        ]
        # for cost to date
        time_windows += [(first_date, date.today() - timedelta(days=1))]
        # first to last date
        time_windows += [(first_date, last_date)]
    # all stages
    stages = [
        (product.discovery_date, product.alpha_date),
        (product.alpha_date, product.beta_date),
        (product.beta_date, product.live_date),
        (product.live_date, product.end_date)
    ]
    time_windows += [
        (start, end - timedelta(days=1))
        for start, end in stages
        if start and end
    ]
    # financial years
    time_windows += [
        financial_year_tuple(date.today().year + offset)
        for offset in range(-2, 2)
    ]
    return time_windows


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['gen', 'rm'],
            help='generate or remove cache'
        )
        parser.add_argument('-p', '--products', nargs='*', type=str)

    @staticmethod
    def generate_cache_for_time_windows(product, calculation_start_date=None):
        """
        call both `stats_between` and `current_fte` with
        flag `ignore_cache=True` for all time windows
        """
        time_windows = get_product_time_windows(product)
        for start, end in time_windows:
            if start and end:
                product.stats_between(
                    start,
                    end,
                    calculation_start_date=calculation_start_date,
                    ignore_cache=True
                )
            product.current_fte(
                start_date=start,
                end_date=end,
                ignore_cache=True
            )

    @staticmethod
    def generate_cache_for_profile(product, calculation_start_date=None):
        """
        call the `profile` method with flag `ignore_cache=True`
        """
        product.profile(
            calculation_start_date=calculation_start_date,
            ignore_cache=True
        )

    @classmethod
    def generate(cls, product):
        """
        generate cache
        :param product: product object
        """
        logging.info('- generating caching for product "%s"', product)
        cls.generate_cache_for_time_windows(
            product,
            calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT)
        cls.generate_cache_for_profile(
            product,
            calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT)

    @staticmethod
    def remove():
        """
        remove cache
        """
        cache.clear()

    def handle(self, *args, **options):
        if options['action'] == 'gen':
            products = Product.objects.visible()
            if options['products']:
                products = products.filter(contains_any('name', options['products']))
                if not products:
                    logging.info('no product found for name %s', options['products'])

            for product in products:
                self.generate(product)
        elif options['action'] == 'rm':
            self.remove()
