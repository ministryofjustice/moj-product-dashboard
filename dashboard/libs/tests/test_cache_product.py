# -*- coding: utf-8 -*-
from decimal import Decimal
from unittest.mock import patch
from datetime import timedelta

from model_mommy import mommy
import pytest

from dashboard.libs import cache_tools
from dashboard.apps.dashboard.management.commands.cache import Command
from dashboard.apps.dashboard.models import Product, Task, Person, Rate
from dashboard.libs.date_tools import parse_date
from dashboard.apps.dashboard.spreadsheets import Products


task_time_ranges = [
    ('2016-01-01', '2016-01-06'),  # 1st finishes later than 2nd
    ('2016-01-03', '2016-01-05'),
    ('2016-01-14', '2016-01-15'),
    ('2016-01-10', '2016-01-20'),  # last starts earlier than the one prior
]
start_date = parse_date(task_time_ranges[0][0])
end_date = parse_date(task_time_ranges[-1][1])
contractor_rate = Decimal('400')
non_contractor_rate = Decimal('350')
man_days = len(task_time_ranges)  # 1 day on each task

discovery_date = start_date
alpha_date = start_date + timedelta(days=5)
beta_date = alpha_date + timedelta(days=5)
live_date = beta_date + timedelta(days=5)


def make_product():
    product = mommy.make(
        Product,
        discovery_date=discovery_date,
        alpha_date=alpha_date,
        beta_date=beta_date,
        live_date=live_date,
        end_date=end_date
    )
    contractor = mommy.make(Person, is_contractor=True)
    non_contractor = mommy.make(Person, is_contractor=False)
    mommy.make(
        Rate,
        start_date=start_date,
        rate=contractor_rate,
        person=contractor
    )
    mommy.make(
        Rate,
        start_date=start_date,
        rate=non_contractor_rate,
        person=non_contractor
    )
    for sd, ed in task_time_ranges:
        mommy.make(
            Task,
            person=contractor,
            product=product,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
        mommy.make(
            Task,
            person=non_contractor,
            product=product,
            start_date=parse_date(sd),
            end_date=parse_date(ed),
            days=1
        )
    return product


class DummyCache:

    def __init__(self):
        self.cache = {}

    def __contains__(self, key):
        return key in self.cache

    def set(self, key, value, timeout):
        self.cache[key] = {'value': value, 'timeout': timeout}

    def get(self, key):
        return self.cache[key]['value']


@pytest.mark.django_db
def test_generate_cache():
    """
    there are 3 cached methods, `profile`, `stats_between`
    and `current_fte`. `profile` depends on both
    `stats_between` and `current_fte`.

    the challenge is when regenerating cache for
    `stats_between` and `current_fte`, all the possible
    values need to be regenerated, otherwise when run
    `profile` it will miss cache and missed cache will
    not be regenerated.
    """
    product = make_product()
    dummy_cache = DummyCache()
    with patch.object(cache_tools, 'cache', dummy_cache):
        # run generate_cache_for_time_windows, which calls
        # `stats_between` and `current_fte` with input of
        # all time_windows of interests
        Command.generate_cache_for_time_windows(product)
        cache_keys_1 = set(dummy_cache.cache.keys())

        # run `profile` should add only 1 more cached
        # result, which is for `profile` itself.
        Command.generate_cache_for_profile(product)
        cache_keys_2 = set(dummy_cache.cache.keys())
        assert cache_keys_1.issubset(cache_keys_2)
        assert len(cache_keys_2 - cache_keys_1) == 1

        # run excel spreadsheet export should not miss
        # any cache
        Products([product])
        cache_keys_3 = set(dummy_cache.cache.keys())
        assert cache_keys_2 == cache_keys_3
