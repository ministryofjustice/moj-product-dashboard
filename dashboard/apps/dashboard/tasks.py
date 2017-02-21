# -*- coding: utf-8 -*-
from datetime import timedelta, date
import functools

from django.core.cache import cache
from django.core.management import call_command
from django.conf import settings

from celery import shared_task, group
from celery.task import periodic_task

from .models import Product
from .management.commands.helpers import logger


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
    timewindow_start_date = date.today() - timedelta(
        days=settings.FLOAT_TASK_SYNC_START_FROM_DAYS_PRIOR_TO_TODAY
    )
    start_date = max(
        [timewindow_start_date, settings.FLOAT_TASK_SYNC_STARTING_POINT]
    )
    call_command('sync', start_date=start_date)
    cache_products.delay()


@shared_task()
@single_instance_task(60*10)
def cache_products():
    tasks = []
    for product in Product.objects.visible():
        tasks.append(cache_product.s(
            product_id=product.pk,
            task_prefix='projet-%s-'
                        % product.pk))
    all_products_task = group(tasks)
    all_products_task.apply_async()


@shared_task()
@single_instance_task(60*10)
def cache_product(product_id):
    product = Product.objects.get(pk=product_id)

    logger.info('- generating caching for product "%s"', product)
    product.profile(
        calculation_start_date=settings.PEOPLE_COST_CALCATION_STARTING_POINT,
        ignore_cache=True
    )
