# -*- coding: utf-8 -*-
"""
utilities for cache
"""
import logging
from hashlib import sha224
from functools import wraps

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


def method_cache(timeout=DEFAULT_TIMEOUT):
    """
    A decorator for caching method on django models.
    param seconds: An optional integer for the timeout in seconds. if not
    specified, the default timeout is used.
    return: a wrapped function
    """
    def inner(method):
        @wraps(method)
        def wrapper(instance, *args, **kwargs):
            key_str = '{}:{}:{}:{}:{}'.format(
                method.__module__,
                method.__name__,
                instance.id,
                args,
                kwargs)
            key = sha224(key_str.encode()).hexdigest()

            if key in cache:
                logger.debug('cache found for key %s', key_str)
                return cache.get(key)

            result = method(instance, *args, **kwargs)
            logger.debug('cache generated for key %s', key_str)
            cache.set(key, result, timeout)
            return result
        return wrapper
    return inner
