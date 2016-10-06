# -*- coding: utf-8 -*-
from .base import *

SECURE_SSL_REDIRECT = False

if 'dashboard.apps.testing' not in INSTALLED_APPS:
    INSTALLED_APPS += ['dashboard.apps.testing']

if 'django_extensions' not in INSTALLED_APPS:
    INSTALLED_APPS += ['django_extensions']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'caching-test': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
