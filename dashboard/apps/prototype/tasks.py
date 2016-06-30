# -*- coding: utf-8 -*-
from datetime import timedelta, date

from django.core.management import call_command

from celery.task import periodic_task


@periodic_task(run_every=timedelta(minutes=5))
def sync_float():
    ninty_days_ago = date.today() - timedelta(days=90)
    call_command('sync', s=ninty_days_ago.strftime('%Y-%m-%d'))
