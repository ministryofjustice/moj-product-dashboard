# -*- coding: utf-8 -*-
import urllib.parse

from django.utils.html import strip_tags
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.template.loader import get_template
from django.core.mail import send_mail

from .models import Person


@receiver(post_save, sender=Person)
def send_email_on_person_creation(sender, **kwargs):
    if not kwargs.get('created'):
        return

    person = kwargs['instance']
    emails = [
        u.email for u in User.objects.filter(
            groups__name=settings.FINANCE_GROUP_NAME,
            email__isnull=False)
        if u.email
    ]
    emails += [a[1] for a in settings.ADMINS if a[1] not in emails]
    template = get_template('email/new_person_created.txt')
    html = template.render({
        'person': person,
        'admin_url': urllib.parse.urljoin(settings.BASE_URL, person.admin_url)
    })
    text = strip_tags(html)
    send_mail(
        'MoJ Product Tracker - A new person was just added',
        text,
        settings.DEFAULT_FROM_EMAIL,
        emails,
        html_message=html
    )
