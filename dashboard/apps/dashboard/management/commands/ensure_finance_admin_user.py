#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):

    help = 'Create a finance admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '-u', '--username', default='finance', help='user name')
        parser.add_argument(
            '-p', '--password', default='Password1', help='password')
        parser.add_argument(
            '-f', '--force', action='store_true',
            help='create a new finance admin user even if one already exists'
        )

    def handle(self, *args, **options):
        finance_users = User.objects.filter(groups__name='Finance')
        admin_users = User.objects.filter(groups__name='Admin')
        existing = set(finance_users) & set(admin_users)
        # if one already exists and no enforcing of a new one, do nothing
        if existing and not options['force']:
            self.stdout.write(self.style.WARNING(
                'existing finance admin user(s) found {}'.format(existing)))
            return

        user = User.objects.create_user(
            username=options['username'],
            password=options['password'],
            is_staff=True
        )
        user.groups.add(Group.objects.get(name='Finance'))
        user.groups.add(Group.objects.get(name='Admin'))
        user.save()
        self.stdout.write(self.style.SUCCESS(
            'successfully created finance admin user "{}"'.format(user)))
