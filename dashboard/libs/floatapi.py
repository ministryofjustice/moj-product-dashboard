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
    return {'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json'}


def many(endpoint, token, **params):
    rsp = requests.get('{}/{}'.format(ROOT, endpoint),
                       headers=get_headers(token),
                       params=params)
    rsp.raise_for_status()
    result = rsp.json()
    return result


def one(endpoint, token, id):
    rsp = requests.get('{}/{}/{}'.format(ROOT, endpoint, id),
                       headers=get_headers(token))
    rsp.raise_for_status()
    result = rsp.json()
    return result


def try_endpoints(token):
    for endpoint in ENDPOINTS:
        rsp = requests.get('{}/{}'.format(ROOT, endpoint),
                           headers=get_headers(token))
        print('- {}'.format(endpoint))
        print(rsp.json())
        print('\n')


def main():
    from dashboard.settings import FLOAT_API_TOKEN
    try_endpoints(FLOAT_API_TOKEN)


if __name__ == '__main__':
    main()
