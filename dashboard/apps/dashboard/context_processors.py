# -*- coding: utf-8 -*-
from django.conf import settings


def application(request):  # pragma: no cover
    return settings.APPLICATION_CONTEXT
