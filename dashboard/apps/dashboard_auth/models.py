# -*- coding: utf-8 -*-
import urllib.parse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


class DashboardUser(User):
    class Meta:
        proxy = True
        app_label = 'dashboard_auth'
        auto_created = True

    @property
    def is_finance(self):
        return self.groups.filter(name=settings.FINANCE_GROUP_NAME).exists()


def send_emails_to_finance(instance):
    emails = [u.email for u in
              User.objects.filter(~Q(pk=instance.pk)).filter(
                  groups__name=settings.FINANCE_GROUP_NAME,
                  email__isnull=False,) if u.email]

    emails += [a[1] for a in settings.ADMINS]
    emails = set(emails)

    if emails:
        template = get_template('email/finance_user_added.txt')
        html = template.render({
            'user': instance,
        })
        text = strip_tags(html)

        send_mail(
            'Finance User Added: %s' % instance.email,
            text,
            settings.DEFAULT_FROM_EMAIL,
            emails,
            html_message=html
        )


@receiver(m2m_changed, sender=User.groups.through)
def send_finance_user_email(instance, pk_set, action, model, **kwargs):
    finance_group = model.objects.get(name=settings.FINANCE_GROUP_NAME)

    if action == 'post_add' and finance_group.pk in pk_set:
        send_emails_to_finance(instance)


@receiver(post_save, sender=User)
def send_email_to_new_user(sender, **kwargs):
    user = kwargs['instance']
    if kwargs.get('created') and user.email:
        template = get_template('email/new_user_created.txt')
        path = reverse(
            'password_reset_confirm',
            kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            }
        )
        password_reset_url = urllib.parse.urljoin(settings.BASE_URL, path)
        html = template.render({
            'user': user,
            'password_reset_url': password_reset_url
        })
        text = strip_tags(html)
        send_mail(
            'Product Tracker - Your new user account',
            text,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html
        )
