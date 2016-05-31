#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError

from dashboard.libs.queries import (
    get_areas, get_persons, get_projects, get_tasks, valid_date, tasks_by_person_proj,
    NoMatchFound)
from .helpers import print_person, print_task, logger


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
        try:
            persons = get_persons(options['names'], logger=logger)
        except NoMatchFound as exc:
            raise CommandError(exc.args)
        try:
            areas = get_areas(options['areas'], logger=logger)
        except NoMatchFound as exc:
            raise CommandError(exc.args)
        try:
            projects = get_projects(options['projects'] or [], areas,
                                    logger=logger)
        except NoMatchFound as exc:
            raise CommandError(exc.args)

        tasks = get_tasks(start_date, end_date, logger)
        tasks = tasks_by_person_proj(tasks, persons, projects)
        person_to_task = {}
        for task in tasks:
            person_to_task.setdefault(task.person, []).append(task)
        total_time = 0
        total_money = 0
        for person in person_to_task:
            logger.info('-' * 20)
            print_person(person)
            for task in person_to_task[person]:
                try:
                    time_cost, money_cost = print_task(
                        task, start_date, end_date)
                except ValueError as exc:
                    logger.warning('found data problem in task %s', task)
                    continue
                else:
                    total_time += time_cost
                    total_money += money_cost
        logger.info('-' * 20)
        logger.info('total spendings {:.5f} man days, £ {:.2f}'.format(
            total_time, total_money))
