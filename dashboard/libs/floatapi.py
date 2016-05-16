#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api client for float
"""
import requests
from dashboard.settings import FLOAT_API_TOKEN as TOKEN

ROOT = 'https://api.floatschedule.com/api/v1'

ENDPOINTS = ['projects', 'people', 'tasks', 'holidays',
             'milestones', 'clients', 'accounts']
HEADERS = (
    ('Authorization', 'Bearer {}'.format(TOKEN)),
    ('Accept', 'application/json')
)


def many(endpoint, **params):
    rsp = requests.get('{}/{}'.format(ROOT, endpoint), headers=dict(HEADERS),
                       params=params)
    result = rsp.json()
    return result


def one(endpoint, id):
    rsp = requests.get('{}/{}/{}'.format(ROOT, endpoint, id),
                       headers=dict(HEADERS))
    result = rsp.json()
    return result


def try_endpoints():
    headers = {'Authorization': 'Bearer {}'.format(TOKEN),
               'Accept': 'application/json'}
    for endpoint in ENDPOINTS:
        rsp = requests.get('{}/{}'.format(ROOT, endpoint), headers=headers)
        print('- {}'.format(endpoint))
        print(rsp.json())
        print('\n')


def main():
    try_endpoints()


if __name__ == '__main__':
    main()
