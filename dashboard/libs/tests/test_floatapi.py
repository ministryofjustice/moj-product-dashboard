#!/usr/bin/env python
from unittest.mock import patch

import pytest

from dashboard.libs.floatapi import one, many


@patch('dashboard.libs.floatapi.requests')
def test_one_succeed(requests):
    one('projects', 'token', 1)
    assert requests.get.called


@patch('dashboard.libs.floatapi.requests')
def test_many_succeed(requests):
    many('projects', 'token')
    assert requests.get.called


def test_wrong_endpoint():
    with pytest.raises(ValueError):
        one('invalid-endpoint', 'token', 1)

    with pytest.raises(ValueError):
        many('invalid-endpoint', 'token')
