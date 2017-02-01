#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calculate
"""
from datetime import date, timedelta
import logging

from django.core.management.base import BaseCommand, CommandError

from dashboard.libs.date_tools import parse_date
from dashboard.apps.dashboard.models import Task
from .helpers import (
    print_person, print_task, get_persons, get_products, get_areas,
    NoMatchFound)


class Command(BaseCommand):
    help = 'Calculate'

    def add_arguments(self, parser):
        today = date.today()
        this_monday = today - timedelta(today.weekday())
        this_friday = today + timedelta(4 - today.weekday())
        parser.add_argument('-s', '--start-date', type=parse_date,
                            default=this_monday)
        parser.add_argument('-e', '--end-date', type=parse_date,
                            default=this_friday)
        parser.add_argument('-p', '--products', nargs='*', type=str)
        parser.add_argument('-a', '--areas', nargs='*', type=str)
        parser.add_argument('-n', '--names', nargs='*', type=str)

    @staticmethod
    def _print_tasks(person_to_task, start_date, end_date):
        total_time = 0
        total_money = 0
        for person in person_to_task:
            logging.info('-' * 20)
            print_person(person)
            for task in sorted(person_to_task[person], key=lambda t: t.start_date):
                try:
                    time_cost, money_cost = print_task(
                        task, start_date, end_date)
                except ValueError:
                    logging.warning('found data problem in task %s', task)
                    continue
                else:
                    total_time += time_cost
                    total_money += money_cost
        logging.info('total spendings {:.5f} man days, £ {:.2f}'.format(
            total_time, total_money))

    def handle(self, *args, **options):
        start_date = options['start_date']
        end_date = options['end_date']
        logging.info('time frame start: {} end : {}'.format(
            start_date, end_date))
        try:
            persons = get_persons(options['names'])
        except NoMatchFound as exc:
            raise CommandError(exc.args)
        try:
            areas = get_areas(options['areas'])
        except NoMatchFound as exc:
            raise CommandError(exc.args)
        try:
            products = get_products(options['products'] or [], areas)
        except NoMatchFound as exc:
            raise CommandError(exc.args)

        tasks = Task.objects.between(start_date, end_date)
        if persons:
            tasks = tasks.filter(person__in=persons)
        if products:
            tasks = tasks.filter(product__in=products)
        person_to_task = {}
        for task in tasks:
            person_to_task.setdefault(task.person, []).append(task)
        self._print_tasks(person_to_task, start_date, end_date)
