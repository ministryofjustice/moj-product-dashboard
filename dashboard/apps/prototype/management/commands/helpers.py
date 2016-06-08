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
    people_costs = task.people_costs(start_date, end_date)
    lines.append(
        'spendings in this time frame: {:.5f} days, £{:.2f}'.format(
            time_spent, people_costs))
    for index, line in enumerate(lines):
        if index == 0:
            logger.info('%s- %s', padding, line)
        else:
            logger.info('%s  %s', padding, line)
    return time_spent, people_costs


def get_persons(names, as_filter=True):
    if not names:
        logger.info('people: all')
        if as_filter:
            return []
        else:
            return Person.objects.all()
    persons = Person.objects.filter(contains_any('name', names))
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
    areas = Client.objects.filter(contains_any('name', names))
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

    projects = Project.objects.filter(contains_any('name', names))

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


def contains_any(field, values, ignore_case=True):
    if ignore_case:
        key = '{}__icontains'.format(field)
    else:
        key = '{}__contains'.format(field)

    filter_by_values = Q()
    for value in values:
        filter_by_values |= Q(**{key: value})

    return filter_by_values
