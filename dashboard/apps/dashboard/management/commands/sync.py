#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export from float
"""
import os
import json
from datetime import datetime, date, timedelta
import functools
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from requests.exceptions import HTTPError
import shutil

import dashboard.settings as settings
from dashboard.libs.floatapi import many
from dashboard.apps.dashboard.models import Area, Person, Product, Task
from dashboard.libs.date_tools import get_workdays, parse_date
from .helpers import logger

FLOAT_DATA_DIR = settings.location('../var/float')


def export(token, start_date, weeks, output_dir):
    for endpoint in ['clients', 'people', 'projects', 'accounts']:
        data = many(endpoint, token)
        filename = os.path.join(output_dir, '{}.json'.format(endpoint))
        with open(filename, 'w') as fw:
            fw.write(json.dumps(data, indent=2))

    tasks = many('tasks', token, start_day=start_date, weeks=weeks)
    tasks_filename = os.path.join(output_dir, 'tasks.json')
    with open(tasks_filename, 'w') as fw:
        fw.write(json.dumps(tasks, indent=2))

    active_people = many('people', token, active=1)
    active_people_filename = os.path.join(output_dir, 'people-active.json')
    with open(active_people_filename, 'w') as fw:
        fw.write(json.dumps(active_people, indent=2))


def compare(existing_object, data, ignores=('raw_data',)):
    """
    compare and existing object with some data
    :param existing_object: a django.Model object
    :param data: a dictionary
    :returns: a dictionary showing the differences
    """
    result = {}
    for key, value in data.items():
        if key in ignores:
            continue
        old_value = getattr(existing_object, key)
        if value != old_value:
            setattr(existing_object, key, value)
            result[key] = {'new': value, 'old': old_value}
    return result


def update(existing_object, difference):
    object_type = type(existing_object).__name__
    if difference:
        logger.info('existing %s "%s" has changes "%s", updating',
                    object_type, existing_object, difference)
        existing_object.save()
    else:
        logger.debug('existing %s "%s" has no change, do nothing',
                     object_type, existing_object)


@functools.lru_cache()
def get_account_to_people_mapping(data_dir):
    source = os.path.join(data_dir, 'accounts.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    mapping = {item['account_id']: item['people_id']
               for item in data['accounts']}
    return mapping


def sync_clients(data_dir):
    logger.info('sync clients')
    source = os.path.join(data_dir, 'clients.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    for item in data['clients']:
        useful_data = {
            'float_id': item['client_id'],
            'name': item['client_name'],
            'raw_data': item,
        }
        try:
            client = Area.objects.get(float_id=useful_data['float_id'])
            diff = compare(client, useful_data)
            update(client, diff)
        except Area.DoesNotExist:
            client = Area.objects.create(**useful_data)
            logger.info('new client found "%s"', client)
            client.save()


def sync_people(data_dir):
    logger.info('sync people')
    source1 = os.path.join(data_dir, 'people.json')
    source2 = os.path.join(data_dir, 'people-active.json')
    with open(source1, 'r') as sf:
        data = json.loads(sf.read())
    with open(source2, 'r') as sf:
        active_people = {
            p['people_id']: p for p in json.loads(sf.read())['people']}

    for item in data['people']:
        useful_data = {
            'float_id': item['people_id'],
            'name': item['name'],
            'email': item['email'],
            'job_title': item['job_title'],
            'is_contractor': item['contractor'],
            'avatar': item['avatar_file'],
            'raw_data': item,
            'is_current': item['people_id'] in active_people
        }
        try:
            person = Person.objects.get(float_id=useful_data['float_id'])
            diff = compare(person, useful_data)
            update(person, diff)
        except Person.DoesNotExist:
            person = Person.objects.create(**useful_data)
            logger.info('new person found "%s"', person)
            person.save()


def sync_projects(data_dir):
    logger.info('sync projects')
    source = os.path.join(data_dir, 'projects.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    float_ids = []
    for item in data['projects']:
        float_client_id = item['client_id']
        float_id = item['project_id']
        float_ids.append(float_id)
        if float_client_id:
            area_id = Area.objects.get(float_id=float_client_id).id
        else:
            area_id = None
        useful_data = {
            'name': item['project_name'],
            'float_id': float_id,
            'is_billable': item['non_billable'] == '0',
            'description': item['description'],
            'area_id': area_id,
            'raw_data': item,
        }
        try:
            product = Product.objects.get(float_id=float_id)
            diff = compare(product, useful_data)
            update(product, diff)
        except Product.DoesNotExist:
            product = Product.objects.create(**useful_data)
            logger.info('new product found "%s"', product)
            product.save()
    deleted_projects = Product.objects.exclude(float_id__in=float_ids)
    for deleted in deleted_projects:
        if not deleted.tasks.all():
            logger.info(
                'found deleted product float_id=%s "%s"',
                deleted.float_id, deleted)
            deleted.delete()


def sync_tasks(start_date, end_date, data_dir):
    logger.info('sync tasks')
    source = os.path.join(data_dir, 'tasks.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    float_ids = []
    for item in data['people']:
        float_person_id = item['people_id']
        person_id = Person.objects.get(float_id=float_person_id).id
        for task in item['tasks']:
            float_project_id = task['project_id']
            product_id = Product.objects.get(float_id=float_project_id).id
            task_start_date = datetime.strptime(
                task['start_date'], '%Y-%m-%d').date()
            task_end_date = datetime.strptime(
                task['end_date'], '%Y-%m-%d').date()
            if task_start_date > task_end_date:
                logger.warning(
                    'found task with start date greater than end date. skip!'
                    ' task data %s', task)
                continue
            workdays = get_workdays(task_start_date, task_end_date)
            float_id = task['task_id']
            float_ids.append(float_id)
            useful_data = {
                'name': task['task_name'],
                'float_id': float_id,
                'person_id': person_id,
                'product_id': product_id,
                'start_date': task_start_date,
                'end_date': task_end_date,
                'days': workdays * Decimal(task['hours_pd']) / Decimal('8'),
                'raw_data': task,
            }
            try:
                task = Task.objects.get(float_id=float_id)
                diff = compare(task, useful_data)
                update(task, diff)
            except Task.DoesNotExist:
                task = Task.objects.create(**useful_data)
                logger.info('new Task found "%s"', task)
                task.save()
    deleted_tasks = Task.objects.filter(
        Q(start_date__gte=start_date, start_date__lt=end_date)
    ).exclude(float_id__in=float_ids)
    for deleted in deleted_tasks:
        logger.info(
            'found deleted task float_id=%s "%s"', deleted.float_id, deleted)
        deleted.delete()


def sync(start_date, end_date, data_dir):
    sync_clients(data_dir)
    sync_people(data_dir)
    sync_projects(data_dir)
    sync_tasks(start_date, end_date, data_dir)


def ensure_directory(d):
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


class Command(BaseCommand):
    help = 'Sync with float'
    output = ['accounts.json', 'clients.json',
              'projects.json', 'tasks.json',
              'people.json', 'people-active.json']

    def add_arguments(self, parser):
        today = date.today()
        three_month_in_the_past = today - timedelta(days=90)
        parser.add_argument('-s', '--start-date', type=parse_date,
                            default=three_month_in_the_past)
        parser.add_argument('-w', '--weeks', type=int, default=13)
        parser.add_argument('-t', '--token', type=str)
        parser.add_argument('-o', '--output-dir', type=ensure_directory,
                            default=self._default_output_dir())

    @staticmethod
    def _default_output_dir():
        output_dir = os.path.join(
            FLOAT_DATA_DIR, datetime.now().strftime('%y%m%d%H%M'))
        return ensure_directory(output_dir)

    def _get_token(self, token):
        if token:
            return token
        try:
            return settings.FLOAT_API_TOKEN
        except AttributeError:
            raise CommandError(
                'float api token is not supplied. please either specify it'
                ' as a command argument or as FLOAT_API_TOKEN in settings.')

    def _has_all_files(self, output_dir):
        """
        check if all files are present in the output directory
        """
        for filename in self.output:
            if not os.path.isfile(os.path.join(output_dir, filename)):
                return False
        return True

    def handle(self, *args, **options):
        token = self._get_token(options['token'])

        start_date = options['start_date']
        # float effectively takes the prior Monday as the start_date
        start_date = start_date - timedelta(days=start_date.weekday())
        weeks = options['weeks']
        end_date = start_date + timedelta(days=weeks * 7)

        output_dir = options['output_dir']
        if self._has_all_files(output_dir):
            logger.info(
                ('- found already exported Float data in direcotry %s.'
                 ' skip downloading.'), output_dir)
        else:
            logger.info(
                ('- export data from Float from %s for %s weeks to %s.'
                 ' dump the data to directoy %s'),
                start_date, weeks, end_date, output_dir)

            try:
                export(token, start_date, weeks, output_dir)
            except HTTPError as exc:
                raise CommandError(exc.args)
        logger.info('- sync database with exported Float data.')
        sync(start_date, end_date, data_dir=output_dir)
        shutil.rmtree(output_dir, ignore_errors=True)
        logger.info('- job complete.')
