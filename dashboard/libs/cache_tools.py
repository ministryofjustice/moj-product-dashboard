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


class method_cache:
    """
    A decorator for caching method on django models.
    if not specified, the default timeout is used.
    """

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        """
        param timeout: an integer for the timeout in seconds
        or None for cache forever.
        this is the same behaviour as the timeout on cache.set.
        """
        self.timeout = timeout

    @staticmethod
    def cache_key(method, instance, *args, **kwargs):
        key_str = '{}:{}:{}:{}:{}'.format(
            method.__module__,
            method.__name__,
            instance.id,
            args,
            kwargs)
        key = sha224(key_str.encode()).hexdigest()
        return key

    def __call__(self, method):
        """
        return: a wrapped function
        """
        @wraps(method)
        def wrapper(instance, *args, **kwargs):
            key = self.cache_key(method, instance, *args, **kwargs)
            if key in cache:
                logger.debug('cache found for key %s', key)
                return cache.get(key)

            result = method(instance, *args, **kwargs)
            logger.debug('cache generated for key %s', key)
            cache.set(key, result, self.timeout)
            return result
        return wrapper
