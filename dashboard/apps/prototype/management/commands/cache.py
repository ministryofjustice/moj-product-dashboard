#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
command for generating and clearing cache
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.core.cache import cache

from dashboard.apps.prototype.models import Project
from dashboard.libs.date_tools import slice_time_window
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
        for project in Project.objects.visible():
            logger.info('- generating caching for project "%s"', project)
            logger.info('  * spendings each month')
            project.profile(freq='MS')
            if not project.first_task:
                # no task no cost
                continue
            start_date = project.first_task.start_date
            end_date = project.last_task.end_date
            # monthly people costs
            time_windows = slice_time_window(start_date, end_date, freq='MS')
            # to date people costs
            time_windows.append((start_date, date.today()))
            for sdate, edate in time_windows:
                project.people_costs(
                    sdate, edate,
                    ignore_cache=True)
                project.people_costs(
                    sdate, edate,
                    contractor_only=True,
                    ignore_cache=True)
                project.people_costs(
                    sdate, edate,
                    non_contractor_only=True,
                    ignore_cache=True)

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
