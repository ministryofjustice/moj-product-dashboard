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


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['gen', 'rm'],
            help='generate or remove cache'
        )

    def generate(self):
        """
        generate cache
        """
        for product in Product.objects.visible():
            logging.info('- generating caching for product "%s"', product)
            product.profile(
                calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT,
                ignore_cache=True
            )

    def remove(self):
        """
        remove cache
        """
        cache.clear()

    def handle(self, *args, **options):
        if options['action'] == 'gen':
            self.generate()
        elif options['action'] == 'rm':
            self.remove()
