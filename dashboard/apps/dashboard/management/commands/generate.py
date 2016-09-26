#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
random rate generator
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from dashboard.apps.dashboard.models import Rate
from dashboard.libs.rate_generator import gen_rates, get_reference_rate
from dashboard.libs.date_tools import parse_date
from .helpers import logger, get_persons, NoMatchFound


class Command(BaseCommand):
    help = 'Generate random rate data'

    def add_arguments(self, parser):
        a_year_today = date.today() + timedelta(days=365)
        parser.add_argument('-s', '--start-date', type=parse_date,
                            default=date(2015, 1, 1))
        parser.add_argument('-e', '--end-date', type=parse_date,
                            default=a_year_today)
        parser.add_argument('-n', '--names', nargs='*', type=str)
        parser.add_argument(
            '--min', type=float, default=0.90,
            help='minimum percentage of reference rate, default to 0.8')
        parser.add_argument(
            '--max', type=float, default=1.20,
            help='maxmum percentage of reference rate, default to 1.2')
        parser.add_argument(
            '-f', '--freq', default='2QS',
            help=('offset aliases supported by pandas, default to 2QS,'
                  ' i.e. every 2 quarters'))

    def handle(self, *args, **options):
        try:
            people = get_persons(options['names'], as_filter=False)
        except NoMatchFound as exc:
            raise CommandError(exc.args)
        start_date = options['start_date']
        end_date = options['end_date']
        freq = options['freq']
        for person in people:
            logger.info('-' * 20)
            if person.is_contractor:
                logger.info('name: %s, job title: %s (contractor)',
                            person.name, person.job_title)
            else:
                logger.info('name: %s, job title: %s',
                            person.name, person.job_title)
            reference_rate = get_reference_rate(
                person.job_title, person.is_contractor)
            logger.info('reference rate: %s', reference_rate)
            logger.info('start: %s end: %s', start_date, end_date)
            rates = gen_rates(start_date,
                              end_date,
                              freq,
                              reference_rate * options['min'],
                              reference_rate * options['max'])
            logger.info('randomly generated rates:')
            logger.info(rates)
            for sdate, rate in rates.items():
                try:
                    Rate.objects.create(person=person,
                                        start_date=sdate.date(),
                                        rate=Decimal(str(rate)))
                except IntegrityError:
                    logger.info(
                        'found rate for %s with start_date %s already. skip.',
                        person, sdate.date())
