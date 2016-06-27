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


@patch.object(cache_tools, 'cache', locmem_cache)
def test_method_cache():
    mock_obj = MockModel()

    args = (1, 2, 3)
    kw = {'x': 4, 'y': 5}
    cache_key = cache_tools.method_cache.cache_key(
        MockModel.cached_method, mock_obj, *args, **kw)
    locmem_cache.delete(cache_key)

    for i in range(10):
        assert mock_obj.cached_method(*args, **kw) == (args, kw)

    # run 10 times and the only the 1st time should call
    # the real function and the rest hit the cache.
    mock_obj.echo.assert_called_once_with(*args, **kw)

    for i in range(3):
        assert mock_obj.non_cached_method(*args, **kw) == (args, kw)

    # non cached method should call the real function always
    assert mock_obj.echo.call_count == 4
