#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import datetime, date, timedelta

from django.core.management.base import BaseCommand, CommandError
# from django.db.models import Q

# from dashboard.apps.prototype.models import Task, Person, Project, Client

from dashboard.libs.queries import get_areas, get_persons, get_projects, get_tasks, valid_date, filter_projects_by_area


def print_person(person, padding=''):
    if person.is_contractor:
        line = '{}, {} (contractor)'.format(
            person.name, person.job_title,
            person.job_title)
    else:
        line = '{}, {} (civil servant)'.format(
            person.name, person.job_title,
            person.job_title)
    print('{}{}'.format(padding, line))


def print_task(task, start_date, end_date, padding='  '):
    lines = []
    lines.append('task name: {}'.format(task.name or 'N/A'))
    if task.project.is_billable:
        lines.append('project: {}, area: {}'.format(
            task.project, task.project.client.name))
    else:
        lines.append('project: {} (non-billable), area: {}'.format(
            task.project, task.project.client.name))
    lines.append('task start: {}, end: {}, total: {:.5f} working days'.format(
        task.start_date, task.end_date, task.days))
    time_spent = task.time_spent(start_date, end_date)
    lines.append(
        'time spent in this time frame: {:.5f} days'.format(time_spent))
    for index, line in enumerate(lines):
        if index == 0:
            print('{}- {}'.format(padding, line))
        else:
            print('{}  {}'.format(padding, line))


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
        print('time frame start: {} end : {}'.format(start_date, end_date))

        persons = get_persons(options['names'])
        print('people: {}'.format(', '.join([p.name for p in persons]))) if persons else print('people: all')

        areas = get_areas(options['areas'])
        print('areas: {}'.format(', '.join([p.name for p in areas]))) if areas else print('areas: all')

        projects = get_projects(options['projects'] or [], options['areas'] or [])
        print('projects: {}'.format(', '.join([p.name for p in projects]))) if projects else print('projects: all')

        tasks = get_tasks(start_date, end_date)

        if persons:
            tasks = tasks.filter(person__in=persons)
        if projects:
            tasks = tasks.filter(project__in=projects)
        person_to_task = {}
        for task in tasks:
            person_to_task.setdefault(task.person, []).append(task)
        for person in person_to_task:
            print('-' * 20)
            print_person(person)
            for task in person_to_task[person]:
                print_task(task, start_date, end_date)
