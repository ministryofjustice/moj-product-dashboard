# -*- coding: utf-8 -*-
from datetime import timedelta, date
import functools

from django.core.cache import cache
from django.core.management import call_command

from celery import shared_task
from celery.task import periodic_task


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, "true", timeout)
            release_lock = lambda: cache.delete(lock_id)
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
    call_command('sync', s=ninety_days_ago.strftime('%Y-%m-%d'))
    cache_projects.delay()


@shared_task()
@single_instance_task(60*10)
def cache_projects():
    call_command('cache', 'gen')
