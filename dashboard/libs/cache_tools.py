# -*- coding: utf-8 -*-
"""
utilities for cache
"""
import logging
from hashlib import sha224
from functools import wraps
import pickle
import inspect

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


def cache_key(function, instance, args, kwargs):
    """
    for this example function
    >>> def add(x, y, z=3):
    >>>     return x + y + z
    all these forms should generate the same cache key:
    >>> add(1, 2)
    >>> add(1, 2, 3)
    >>> add(1, 2, z=3)
    >>> add(1, y=2, z=3)
    >>> add(x=1, y=2, z=3)
    and these should raise a TypeError
    >>> add(1)  # missing argument
    >>> add(1, 2, 3, z=4)  # multiple values
    >>> add(1, 2, foo=4)  # unexpected keyword argument
    :returns: str key
    :raises: PickingError, ValueError
    """
    key_tuple = (
        function.__module__,
        function.__name__,
        instance.id,
        inspect_arguments(function, args, kwargs)
    )
    key = sha224(pickle.dumps(key_tuple)).hexdigest()
    logger.debug('cache key %s for object %s ', key, key_tuple)
    return key


def inspect_positional_arguments(parameters, args):
    """
    inspect positional arguments
    """
    positional_or_keyword_params = [
        (name, param)
        for name, param in parameters.items()
        if param.kind == param.POSITIONAL_OR_KEYWORD
    ]
    # *args
    var_positional = [
        (name, param)
        for name, param in parameters.items()
        if param.kind == param.VAR_POSITIONAL
    ]

    result = {
        name: arg
        for (name, param), arg in
        zip(positional_or_keyword_params, args)
    }

    if var_positional:
        name, param = var_positional[0]
        result[name] = tuple(args[len(result):]) or param.empty
    elif len(result) < len(args):
        error = 'function takes at most {} positional arguments but {} were given'.format(
            len(positional_or_keyword_params),
            len(args)
        )
        raise TypeError(error)
    return result


def inspect_keyword_arguments(parameters, kwargs):
    options = {
        name: param
        for name, param in parameters.items()
        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
    }

    result = {
        name: value for name, value in kwargs.items()
        if name in options
    }

    for name, param in parameters.items():
        # **kwargs
        if param.kind == param.VAR_KEYWORD:
            var_keyword = name, param
            break
    else:
        var_keyword = None

    if var_keyword:
        name, param = var_keyword
        result[name] = {
            k: v for k, v in kwargs.items()
            if k not in result
        } or param.empty
    elif len(result) < len(kwargs):
        unexpected = set(kwargs.keys()) - set(result.keys())
        error = 'unexpected keyword arguments {}'.format(','.join(unexpected))
        raise TypeError(error)
    return result


def inspect_arguments(function, args, kwargs):
    """
    inspect function signature together with arguments by the caller.
    :param function: function to whose arguments is to be inspected
    :param args: tuple of positional arguments
    :param kwargs: dict of keyword arguments
    :returns: dict for the mapping of argument name to value
    :raises: TypeError
    """
    parameters = inspect.signature(function).parameters
    positional_args = inspect_positional_arguments(parameters, args)
    keyword_args = inspect_keyword_arguments(parameters, kwargs)

    overlap = set(positional_args.keys()) & set(keyword_args.keys())
    if overlap:
        raise TypeError('function got multiple values for arguments {}'.format(','.join(overlap)))

    args_with_default_value = {}
    missing_args = []
    for name, param in parameters.items():
        if name not in positional_args and name not in keyword_args:
            if param.default != param.empty:
                args_with_default_value[name] = param.default
            else:
                missing_args.append(name)
    if missing_args:
        raise TypeError('missing arguments {}'.format(','.join(missing_args)))
    return {**positional_args, **keyword_args, **args_with_default_value}


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

    def __call__(self, method):
        """
        return: a wrapped function
        """
        @wraps(method)
        def wrapper(instance, *args, **kwargs):
            ignore_cache = kwargs.pop('ignore_cache', False)

            try:
                key = cache_key(
                    method,
                    instance,
                    (None,) + args,  # None for first param `self`
                    kwargs
                )
            except Exception as exc:
                logger.exception('generate cache_key failed')
                return method(instance, *args, **kwargs)

            if not ignore_cache and key in cache:
                logger.debug('cache found for key %s', key)
                return cache.get(key)

            if ignore_cache:
                logger.debug('cache ignored')
            result = method(instance, *args, **kwargs)
            logger.debug('cache generated for key %s', key)
            cache.set(key, result, self.timeout)
            return result
        return wrapper
