import logging
from datetime import datetime

from django.db.models import Q

from dashboard.apps.prototype.models import Task, Person, Project, Client


class NoMatchFound(Exception):
    pass


def valid_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def get_dates(start_date, end_date):
    if start_date:
        start_date = valid_date(start_date)
    else:
        start_date = valid_date('2015-01-01')
    if end_date:
        end_date = valid_date(end_date)
    else:
        end_date = valid_date(datetime.date())

    return start_date, end_date


def get_persons(names, as_filter=True, logger=None):
    if not logger:
        logger = logging
    if not names:
        logger.info('people: all')
        if as_filter:
            return []
        else:
            return Person.objects.all()
    query = Q()
    for item in [Q(name__icontains=name) for name in names]:
        query |= item
    persons = Person.objects.filter(query)
    if not persons:
        raise NoMatchFound(
            'could not find any person with name(s) {}'.format(
                ','.join(names)))
    logger.info('people: {}'.format(', '.join([p.name for p in persons])))
    return persons


def get_areas(names, as_filter=True, logger=None):
    if not logger:
        logger = logging
    if not names:
        logger.info('areas: all')
        if as_filter:
            return []
        else:
            return Client.objects.all()
    query = Q()
    for item in [Q(name__icontains=name) for name in names]:
        query |= item
    areas = Client.objects.filter(query)
    if not areas:
        raise NoMatchFound(
            'could not find any area with name(s) {}'.format(
                ','.join(names)))
    logger.info('areas: {}'.format(', '.join([p.name for p in areas])))
    return areas


def get_projects(names, areas, as_filter=True, logger=None):
    if not logger:
        logger = logging
    if not names and not areas:
        logger.info('projects: all')
        if as_filter:
            return []
        else:
            return Project.objects.all()

    filter_by_name = Q()
    for item in [Q(name__icontains=name) for name in names]:
        filter_by_name |= item
    projects = Project.objects.filter(filter_by_name)

    if areas:
        if not isinstance(areas[0], Client):
            areas = get_areas(areas)
        projects = projects.filter(client__in=areas)

    if not projects:
        area_names = ','.join([area.name for area in areas]) or 'all'
        raise NoMatchFound(
            ('could not find any project with name(s) {} and area(s) {}'
             ).format(','.join(names), area_names))
    logger.info('projects: {}'.format(', '.join([p.name for p in projects])))
    return projects


def get_all_projects(names):

    if not names:
        return []

    filter_by_name = Q()
    for item in [Q(name__icontains=name) for name in names]:
        filter_by_name |= item
    projects = Project.objects.filter(filter_by_name)

    if not projects:
        raise NoMatchFound(
            ('could not find any project with name(s) {}'
             ).format(','.join(names)))
    return projects


def get_tasks(start_date, end_date, logger=None):

    if not logger:
        logger = logging

    tasks = Task.objects.filter(
        Q(start_date__gte=start_date, start_date__lte=end_date) |
        Q(end_date__gte=start_date, end_date__lte=end_date) |
        Q(start_date__lt=start_date, end_date__gt=end_date)
    )

    return tasks
