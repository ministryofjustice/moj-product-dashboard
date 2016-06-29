# -*- coding: utf-8 -*-
from .base import *


INSTALLED_APPS += ['django_extensions', 'dashboard.apps.testing']
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'caching-test': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
