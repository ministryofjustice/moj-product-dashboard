#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export from float
"""
import os
import json
from datetime import datetime, date, timedelta
import logging
import functools
from decimal import Decimal

from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from requests.exceptions import HTTPError

from dashboard.settings import location
from dashboard.libs.floatapi import many
from dashboard.apps.prototype.models import Client, Person, Project, Task

START_DATE = date(year=2015, month=1, day=1)
VAR = location('../var')
FLOAT_DATA_DIR = os.path.join(VAR, 'float')

if not os.path.isdir(FLOAT_DATA_DIR):
    os.makedirs(FLOAT_DATA_DIR)


def get_logger():
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'basic': {'format': '%(asctime)s - %(levelname)s - %(message)s'},
            'simple': {'format': '%(message)s'},
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'output.log',
                'formatter': 'basic'
            },
        },
        'loggers': {
            __name__: {
                'handlers': ['console', 'file'],
                'level': 'DEBUG'
            }
        }
    }
    logging.config.dictConfig(LOGGING)
    return logging.getLogger(__name__)

logger = get_logger()


def export(start_date, weeks):
    for endpoint in ['clients', 'people', 'projects', 'accounts']:
        data = many(endpoint)
        filename = os.path.join(FLOAT_DATA_DIR, '{}.json'.format(endpoint))
        with open(filename, 'w') as fw:
            fw.write(json.dumps(data, indent=2))
    tasks = many('tasks', start_day=start_date, weeks=weeks)
    tasks_filename = os.path.join(FLOAT_DATA_DIR, 'tasks.json')
    with open(tasks_filename, 'w') as fw:
        fw.write(json.dumps(tasks, indent=2))


def compare(existing_object, data):
    """
    compare and existing object with some data
    :param existing_object: a django.Model object
    :param data: a dictionary
    :returns: a dictionary showing the differences
    """
    result = {}
    for key, value in data.items():
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
def get_account_to_people_mapping():
    source = os.path.join(FLOAT_DATA_DIR, 'accounts.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    mapping = {item['account_id']: item['people_id']
               for item in data['accounts']}
    return mapping


def sync_clients():
    logger.info('sync clients')
    source = os.path.join(FLOAT_DATA_DIR, 'clients.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    for item in data['clients']:
        useful_data = {
            'float_id': item['client_id'],
            'name': item['client_name'],
        }
        try:
            client = Client.objects.get(float_id=useful_data['float_id'])
            diff = compare(client, useful_data)
            update(client, diff)
        except Client.DoesNotExist:
            client = Client.objects.create(**useful_data)
            logger.info('new client found "%s"', client)
            client.save()


def sync_people():
    logger.info('sync people')
    source = os.path.join(FLOAT_DATA_DIR, 'people.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    for item in data['people']:
        useful_data = {
            'float_id': item['people_id'],
            'name': item['name'],
            'email': item['email'],
            'avatar': item['avatar_file']
        }
        try:
            person = Person.objects.get(float_id=useful_data['float_id'])
            diff = compare(person, useful_data)
            update(person, diff)
        except Person.DoesNotExist:
            person = Person.objects.create(**useful_data)
            logger.info('new person found "%s"', person)
            person.save()


def sync_projects():
    logger.info('sync projects')
    account_to_people = get_account_to_people_mapping()
    source = os.path.join(FLOAT_DATA_DIR, 'projects.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    for item in data['projects']:
        float_client_id = item['client_id']
        if float_client_id:
            client_id = Client.objects.get(float_id=float_client_id).id
        else:
            client_id = None
        pm_account_id = item['project_managers'][0]['account_id']
        project_manager_id = Person.objects.get(
            float_id=account_to_people[pm_account_id]).id
        useful_data = {
            'name': item['project_name'],
            'float_id': item['project_id'],
            'description': item['description'],
            'client_id': client_id,
            'project_manager_id': project_manager_id
        }
        try:
            project = Project.objects.get(float_id=useful_data['float_id'])
            diff = compare(project, useful_data)
            update(project, diff)
        except Project.DoesNotExist:
            project = Project.objects.create(**useful_data)
            logger.info('new project found "%s"', project)
            project.save()


def sync_tasks():
    logger.info('sync tasks')
    source = os.path.join(FLOAT_DATA_DIR, 'tasks.json')
    with open(source, 'r') as sf:
        data = json.loads(sf.read())
    for item in data['people']:
        float_person_id = item['people_id']
        person_id = Person.objects.get(float_id=float_person_id).id
        for task in item['tasks']:
            float_project_id = task['project_id']
            project_id = Project.objects.get(float_id=float_project_id).id
            start_date = timezone.make_aware(
                datetime.strptime(task['start_date'], '%Y-%m-%d'),
                timezone.get_current_timezone())
            end_date = timezone.make_aware(
                datetime.strptime(task['end_date'], '%Y-%m-%d'),
                timezone.get_current_timezone())
            useful_data = {
                'name': task['task_name'],
                'float_id': task['task_id'],
                'person_id': person_id,
                'project_id': project_id,
                'start_date': start_date,
                'end_date': end_date,
                'days': Decimal(task['total_hours']) / 8,
            }
            try:
                task = Task.objects.get(float_id=useful_data['float_id'])
                diff = compare(task, useful_data)
                update(task, diff)
            except Task.DoesNotExist:
                task = Task.objects.create(**useful_data)
                logger.info('new Task found "%s"', task)
                task.save()


def valid_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


class Command(BaseCommand):
    help = 'Sync with float'

    def add_arguments(self, parser):
        today = date.today()
        one_month_in_the_past = today - timedelta(days=30)
        three_month_in_future = today + timedelta(days=90)
        parser.add_argument('-s', '--start-date', type=valid_date,
                            default=one_month_in_the_past)
        parser.add_argument('-e', '--end-date', type=valid_date,
                            default=three_month_in_future)

    def handle(self, *args, **options):
        start_date = options['start_date']
        end_date = options['end_date']
        if start_date > end_date:
            raise CommandError(
                'start_date {} is greater than end_date {}'.format(
                    start_date, end_date))
        logger.info('- export data from float for date range %s to %s',
                    start_date, end_date)
        try:
            export(start_date, end_date)
        except HTTPError as exc:
            raise CommandError(exc.args)
        logger.info('- sync database with float data')
        sync()


def sync():
    sync_clients()
    sync_people()
    sync_projects()
    sync_tasks()
