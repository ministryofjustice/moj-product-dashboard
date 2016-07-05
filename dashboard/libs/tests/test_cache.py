# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from django.core.cache import caches

from dashboard.libs import cache_tools

locmem_cache = caches['caching-test']


def echo(*arg, **kw):
    return (arg, kw)


class MockModel(object):

    def __init__(self):
        self.id = id(self)
        self.echo = Mock(side_effect=echo)

    @cache_tools.method_cache()
    def cached_method(self, *arg, **kw):
        return self.echo(*arg, **kw)

    def non_cached_method(self, *arg, **kw):
        return self.echo(*arg, **kw)


def call_ten_times(method, instance, args, kw):
    cache_key = cache_tools.method_cache.cache_key(
        method, instance, *args, **kw)
    locmem_cache.delete(cache_key)

    for i in range(10):
        method(*args, **kw) == (args, kw)


@patch.object(cache_tools, 'cache', locmem_cache)
def test_method_cache_applied():
    mock_obj = MockModel()
    args = (1, 2, 3)
    kw = {'x': 4, 'y': 5}

    # run 10 times and the only the 1st time should call
    # the real function and the rest hit the cache.
    call_ten_times(mock_obj.cached_method, mock_obj, args, kw)
    assert mock_obj.echo.call_count == 1
    mock_obj.echo.assert_called_once_with(*args, **kw)


@patch.object(cache_tools, 'cache', locmem_cache)
def test_method_cache_not_applied():
    mock_obj = MockModel()
    args = (1, 2, 3)
    kw = {'x': 4, 'y': 5}

    call_ten_times(mock_obj.non_cached_method, mock_obj, args, kw)
    # non cached method should call the real function always
    assert mock_obj.echo.call_count == 10


@patch.object(cache_tools, 'cache', locmem_cache)
def test_method_cache_applied_but_ignored():
    mock_obj = MockModel()
    args = (1, 2, 3)
    kw = {'x': 4, 'y': 5, 'ignore_cache': True}

    # ignore_cache=True means always call the real function
    call_ten_times(mock_obj.cached_method, mock_obj, args, kw)
    assert mock_obj.echo.call_count == 10


@patch.object(cache_tools, 'cache', locmem_cache)
def test_method_cache_applied_and_explictly_not_ignored():
    mock_obj = MockModel()
    args = (1, 2, 3)
    kw = {'x': 4, 'y': 5, 'ignore_cache': False}

    # ignore_cache=False means use the cache if available
    call_ten_times(mock_obj.cached_method, mock_obj, args, kw)
    assert mock_obj.echo.call_count == 1
    kw.pop('ignore_cache')
    mock_obj.echo.assert_called_once_with(*args, **kw)
