#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
command for generating and clearing cache
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.core.cache import cache

from dashboard.apps.prototype.models import Project
from .helpers import logger


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
        for project in Project.objects.all():
            logger.info('- generating caching for project "%s"', project)
            logger.info('  * spendings each month')
            project.profile(freq='MS')
            logger.info('  * spendings for entire project life span')
            project.profile()
            logger.info('  * spendings to date')
            project.profile(end_date=date.today())

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
