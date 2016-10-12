# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


USERS = [
    'test.user@digital.justice.gov.uk',
]


EMAIL_TEXT = """
Hi %s %s.

You have been added as a user to the Product dashboard.

user: %s

Please go to https://prod-product-dashboard.dsd.io/password_reset/ , enter your email and you will be able to set a password and log in.

Thanks.

"""


class Command(BaseCommand):
    help = 'Do not run this'

    def handle(self, *args, **options):
        for email in USERS:
            username, x = email.split('@')
            first_name, last_name = [x.capitalize() for x in username.split('.')]

            if not User.objects.filter(email=email).exists():
                password = str(uuid.uuid4())
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,
                    is_active=True,
                )

                g = Group.objects.get(name='Delivery')
                user.groups.add(g)

                text = EMAIL_TEXT % (
                    first_name,
                    last_name,
                    username
                )

                send_mail(
                    'User Added to Dashboard: %s' % email,
                    text,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )

