# -*- coding: utf-8 -*-
from inspect import Parameter

import pytest
from unittest.mock import Mock, patch

from django.core.cache import caches

from dashboard.libs import cache_tools

locmem_cache = caches['caching-test']
empty = Parameter.empty


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
    cache_key = cache_tools.cache_key(
        method, instance, args, kw)
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


@pytest.mark.parametrize('args, kwargs', [
    ((1, 2), {}),
    ((1, 2, 3), {}),
    ((1, 2), {'z': 3}),
    ((1,), {'y': 2, 'z': 3}),
    ((), {'x': 1, 'y': 2, 'z': 3}),
])
def test_inspect_arguments_positional_or_keyword(args, kwargs):
    def func(x, y, z=3):
        pass

    assert cache_tools.inspect_arguments(
        func, args, kwargs
    ) == {'x': 1, 'y': 2, 'z': 3}


@pytest.mark.parametrize('args, kwargs', [
    ((1, 2, 3, 4), {}),     # too many parameters
    ((1,), {}),             # too few parameters
    ((1, 2, 3), {'z': 4}),  # multiple values for z
    ((1, 2, 3), {'a': 4}),  # unexpected argument a
])
def test_raise_for_inspect_arguments_positional_or_keyword(args, kwargs):
    def func(x, y, z=3):
        pass

    with pytest.raises(TypeError):
        cache_tools.inspect_arguments(func, args, kwargs)


def test_inspect_arguments_var_positional():
    def func(x, y, *args):
        pass

    assert cache_tools.inspect_arguments(
        func, (1, 2, 3, 4), {}
    ) == {'x': 1, 'y': 2, 'args': (3, 4)}


def test_inspect_arguments_func_with_var_keyword():
    def func(x, y, **kw):
        pass

    assert cache_tools.inspect_arguments(
        func, (1, 2), {'kw1': 3, 'kw2': 4}
    ) == {'x': 1, 'y': 2, 'kw': {'kw1': 3, 'kw2': 4}}


@pytest.mark.parametrize('args, kwargs, expected', [
    ((1,), {'y': 2, 'z': 1}, {'x': 1, 'y': 2, 'z': 1}),
    ((1,), {'y': 2}, {'x': 1, 'y': 2, 'z': 1}),
])
def test_inspect_arguments_func_with_keyword_only_parameters(args, kwargs, expected):
    def func(x, *, y, z=1):
        pass
    assert cache_tools.inspect_arguments(
        func, args, kwargs
    ) == expected


@pytest.mark.parametrize('args, kwargs, expected', [
    (
        (1, 2),
        {},
        {'x': 1, 'y': 2, 'z': 3, 'args': empty, 'kw': empty}
    ),
    (
        (1, 2, 3),
        {},
        {'x': 1, 'y': 2, 'z': 3, 'args': (3,), 'kw': empty}
    ),
    (
        (1, 2, 3, 4, 5),
        {'z': 6},
        {'x': 1, 'y': 2, 'z': 6, 'args': (3, 4, 5), 'kw': empty}
    ),
    (
        (1, 2, 3, 4, 5),
        {'z': 6, 'kw1': 7, 'kw2': 8},
        {'x': 1, 'y': 2, 'z': 6, 'args': (3, 4, 5), 'kw': {'kw1': 7, 'kw2': 8}}
    ),
])
def test_inspect_arguments_func_mixed_kinds(args, kwargs, expected):
    def func(x, y, *args, z=3, **kw):
        pass

    assert cache_tools.inspect_arguments(
        func, args, kwargs
    ) == expected
