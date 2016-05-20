#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from dashboard.apps.prototype.models import Task
from .helpers import (valid_date, get_persons, get_areas, get_projects,
                      print_person, print_task, logger)


class Command(BaseCommand):
    help = 'Calculate'

    def add_arguments(self, parser):
        today = date.today()
        this_monday = today - timedelta(today.weekday())
        this_friday = today + timedelta(4 - today.weekday())
        parser.add_argument('-s', '--start-date', type=valid_date,
                            default=this_monday)
        parser.add_argument('-e', '--end-date', type=valid_date,
                            default=this_friday)
        parser.add_argument('-p', '--projects', nargs='*', type=str)
        parser.add_argument('-a', '--areas', nargs='*', type=str)
        parser.add_argument('-n', '--names', nargs='*', type=str)

    def handle(self, *args, **options):
        start_date = options['start_date']
        end_date = options['end_date']
        logger.info('time frame start: {} end : {}'.format(
            start_date, end_date))
        persons = get_persons(options['names'])
        areas = get_areas(options['areas'])
        projects = get_projects(options['projects'] or [], areas)

        tasks = Task.objects.filter(
            Q(start_date__gte=start_date, start_date__lte=end_date) |
            Q(end_date__gte=start_date, end_date__lte=end_date) |
            Q(start_date__lt=start_date, end_date__gt=end_date)
        )
        if persons:
            tasks = tasks.filter(person__in=persons)
        if projects:
            tasks = tasks.filter(project__in=projects)
        person_to_task = {}
        for task in tasks:
            person_to_task.setdefault(task.person, []).append(task)
        for person in person_to_task:
            logger.info('-' * 20)
            print_person(person)
            for task in person_to_task[person]:
                print_task(task, start_date, end_date)
