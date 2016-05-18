#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import datetime, date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from dashboard.apps.prototype.models import Task, Person


def print_person(person, padding=''):
    # TODO do not rely on raw_data
    if person.raw_data['contractor']:
        line = '{}, {} (contractor)'.format(
            person.name, person.raw_data['job_title'],
            person.raw_data['job_title'])
    else:
        line = '{}, {} (civil servant)'.format(
            person.name, person.raw_data['job_title'],
            person.raw_data['job_title'])
    print('{}{}'.format(padding, line))


def print_task(task, start_date, end_date, padding='  '):
    lines = []
    lines.append('task name: {}'.format(task.name or 'N/A'))
    if task.project.is_billable:
        lines.append('project: {}'.format(task.project))
    else:
        lines.append(
            'project: {} (non-billable)'.format(task.project))
    lines.append('task start: {}, end: {}, total: {:.5f} working days'.format(
        task.start_date, task.end_date, task.days))
    time_spent = task.time_spent(start_date, end_date)
    lines.append('time spent in this period: {:.5f} days'.format(time_spent))
    for index, line in enumerate(lines):
        if index == 0:
            print('{}- {}'.format(padding, line))
        else:
            print('{}  {}'.format(padding, line))


def valid_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


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
        parser.add_argument('-n', '--names', nargs='*', type=str)

    def handle(self, *args, **options):
        start_date = options['start_date']
        end_date = options['end_date']
        names = options['names']
        if names:
            queries = [Q(name__icontains=name) for name in names]
            query = queries.pop()
            for item in queries:
                query |= item
            persons = Person.objects.filter(query)
        else:
            persons = []

        print('time frame start: {} end : {}'.format(start_date, end_date))
        if persons:
            print('people: {}'.format(', '.join([p.name for p in persons])))
        else:
            print('people: all')
        tasks = Task.objects.filter(
            Q(start_date__gte=start_date, start_date__lte=end_date) |
            Q(end_date__gte=start_date, end_date__lte=end_date) |
            Q(start_date__lt=start_date, end_date__gt=end_date)
        )
        person_to_task = {}
        for task in tasks:
            person = task.person
            if persons and person in persons or not persons:
                person_to_task.setdefault(task.person, []).append(task)
        for person in person_to_task:
            print('-' * 20)
            print_person(person)
            for task in person_to_task[person]:
                print_task(task, start_date, end_date)
