#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

from dashboard.apps.prototype.models import Task


class Command(BaseCommand):
    help = 'Calculate'

    def handle(self, *args, **options):
        today = date.today()
        weekday = today.weekday()
        first_day_of_last_week = today - timedelta(days=weekday, weeks=1)
        last_day_of_last_week = first_day_of_last_week + timedelta(days=6)
        print('first day')
        print(first_day_of_last_week)
        print('last day')
        print(last_day_of_last_week)
        tasks = Task.objects.filter(start_date__gte=first_day_of_last_week,
                                    start_date__lte=last_day_of_last_week)
        for task in tasks:
            print(task)
