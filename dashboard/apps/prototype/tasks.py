# -*- coding: utf-8 -*-
from datetime import timedelta, date
import functools

from django.core.cache import cache
from django.core.management import call_command

from celery import shared_task, group
from celery.task import periodic_task

from .models import Project
from .management.commands.helpers import logger
from dashboard.libs.date_tools import slice_time_window


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, task_prefix='', **kwargs):
            lock_id = "celery-single-instance-%s%s" % (task_prefix,
                                                       func.__name__)

            def acquire_lock():
                return cache.add(lock_id, "true", timeout)

            def release_lock():
                return cache.delete(lock_id)

            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    release_lock()
        return wrapper
    return task_exc


@periodic_task(run_every=timedelta(minutes=10))
@single_instance_task(60*10)
def sync_float():
    ninety_days_ago = date.today() - timedelta(days=90)
    min_start_date = date(2016, 9, 1)
    start_date = max([ninety_days_ago, min_start_date])
    call_command('sync', start_date=start_date)
    cache_projects.delay()


@shared_task()
@single_instance_task(60*10)
def cache_projects():
    tasks = []
    for project in Project.objects.visible():
        tasks.append(cache_project.s(
            project_id=project.pk,
            task_prefix='projet-%s-'
                        % project.pk))
    all_projects_task = group(tasks)
    all_projects_task.apply_async()


@shared_task()
@single_instance_task(60*10)
def cache_project(project_id):
    project = Project.objects.get(pk=project_id)

    logger.info('- generating caching for project "%s"', project)
    logger.info('  * people costs monthly and on key dates')
    project.profile(freq='MS')
    try:
        start_date = project.first_date
        end_date = project.last_date
    except ValueError:
        return
    # monthly people costs
    time_windows = slice_time_window(
        start_date, end_date, freq='MS', extend=True)
    # people cost to key dates
    time_windows += [
        (start_date, key_date['date']) for key_date
        in project.key_dates(freq='MS').values()
    ]
    for sdate, edate in time_windows:
        project.people_costs(
            sdate, edate,
            ignore_cache=True)
        project.people_costs(
            sdate, edate,
            contractor_only=True,
            ignore_cache=True)
        project.people_costs(
            sdate, edate,
            non_contractor_only=True,
            ignore_cache=True)
