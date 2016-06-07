#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api client for float
"""
import requests


ROOT = 'https://api.floatschedule.com/api/v1'

ENDPOINTS = ['projects', 'people', 'tasks', 'holidays',
             'milestones', 'clients', 'accounts']


def get_headers(token):
    """
    get headers
    :param token: float token
    :return: a dictionary of headers
    """
    return {'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json'}


def many(endpoint, token, **params):
    """
    send a GET request for a list of objects
    :param endpoint: an endpoint from ENDPOINTS list
    :param token: float token
    :return: a dictionary representing the json response
    """
    if endpoint not in ENDPOINTS:
        raise ValueError('unknonw endpoint {}'.format(endpoint))
    rsp = requests.get('{}/{}'.format(ROOT, endpoint),
                       headers=get_headers(token),
                       params=params)
    rsp.raise_for_status()
    result = rsp.json()
    return result


def one(endpoint, token, id):
    """
    send a GET request for one object
    :param endpoint: an endpoint from ENDPOINTS list
    :param token: float token
    :param id: id of the object
    :return: a dictionary representing the json response
    """
    if endpoint not in ENDPOINTS:
        raise ValueError('unknonw endpoint {}'.format(endpoint))
    rsp = requests.get('{}/{}/{}'.format(ROOT, endpoint, id),
                       headers=get_headers(token))
    rsp.raise_for_status()
    result = rsp.json()
    return result


def try_endpoints(token):  # pragma: no cover
    for endpoint in ENDPOINTS:
        rsp = requests.get('{}/{}'.format(ROOT, endpoint),
                           headers=get_headers(token))
        print('- {}'.format(endpoint))
        print(rsp.json())
        print('\n')


def main():  # pragma: no cover
    from dashboard.settings import FLOAT_API_TOKEN
    try_endpoints(FLOAT_API_TOKEN)


if __name__ == '__main__':  # pragma: no cover
    main()
