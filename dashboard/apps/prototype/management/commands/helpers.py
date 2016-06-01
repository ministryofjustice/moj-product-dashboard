"""
some helper functions for creating commands
"""
import logging


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
