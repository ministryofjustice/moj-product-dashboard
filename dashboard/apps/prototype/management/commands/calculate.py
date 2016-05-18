#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from dashboard.apps.prototype.models import Task


class Command(BaseCommand):
    help = 'Calculate'

    def handle(self, *args, **options):
        today = date.today()
        weekday = today.weekday()
        start_date = today - timedelta(days=weekday, weeks=1)
        end_date = start_date + timedelta(days=6)
        print('start day')
        print(start_date)
        print('end day')
        print(end_date)
        tasks = Task.objects.filter(
            Q(start_date__gte=start_date, start_date__lte=end_date) |
            Q(end_date__gte=start_date, end_date__lte=end_date) |
            Q(start_date__lt=start_date, end_date__gt=end_date)
        )
        for task in tasks:
            print(task)
