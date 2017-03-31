#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
command for generating and clearing cache
"""
import logging

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings

from dashboard.apps.dashboard.models import Product
from .helpers import contains_any


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['gen', 'rm'],
            help='generate or remove cache'
        )
        parser.add_argument('-p', '--products', nargs='*', type=str)

    def generate(self, products):
        """
        generate cache
        :param products: list of product objects
        """
        for product in products:
            logging.info('- generating caching for product "%s"', product)
            product.profile(
                calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT,
                ignore_cache=True
            )
            for start, end in [
                    (product.discovery_date, product.alpha_date),
                    (product.alpha_date, product.beta_date),
                    (product.beta_date, product.live_date),
                    (product.live_date, product.end_date)
            ]:
                if start and end:
                    product.stats_between(
                        start,
                        end,
                        calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT,
                        ignore_cache=True
                    )
                product.current_fte(
                    start_date=start,
                    end_date=end,
                    ignore_cache=True
                )

    def remove(self):
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

            self.generate(products)
        elif options['action'] == 'rm':
            self.remove()
