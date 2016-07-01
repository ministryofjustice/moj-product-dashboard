# -*- coding: utf-8 -*-
from datetime import timedelta, date

from django.core.management import call_command

from celery.task import periodic_task
from celery import shared_task


@periodic_task(run_every=timedelta(minutes=15))
def sync_float():
    ninety_days_ago = date.today() - timedelta(days=90)
    call_command('sync', s=ninety_days_ago.strftime('%Y-%m-%d'))
    cache.delay()


@shared_task()
def cache():
    call_command('cache', 'gen')
