"""
some helper functions for creating commands
"""
import logging

from django.db.models import Q

from dashboard.apps.prototype.models import Person, Project, Client


class NoMatchFound(Exception):
    pass


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


def print_person(person, padding=''):
    if person.is_contractor:
        line = '{}, {} (contractor)'.format(
            person.name, person.job_title,
            person.job_title)
    else:
        line = '{}, {} (civil servant)'.format(
            person.name, person.job_title,
            person.job_title)
    logger.info('%s%s', padding, line)


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
    money_spent = task.money_spent(start_date, end_date)
    lines.append(
        'spendings in this time frame: {:.5f} days, £{:.2f}'.format(
            time_spent, money_spent))
    for index, line in enumerate(lines):
        if index == 0:
            logger.info('%s- %s', padding, line)
        else:
            logger.info('%s  %s', padding, line)
    return time_spent, money_spent


def get_persons(names, as_filter=True):
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


def get_areas(names, as_filter=True):
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


def get_projects(names, areas, as_filter=True):
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
