# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.template.loader import get_template
from django.utils.html import strip_tags


class DashboardUser(User):
    class Meta:
        proxy = True
        app_label = 'dashboard_auth'

    @property
    def is_finance(self):
        return self.groups.filter(name=settings.FINANCE_GROUP_NAME).exists()


@receiver(m2m_changed, sender=User.groups.through)
def send_finance_user_email(instance, pk_set, action, model, **kwargs):
    finance_group = model.objects.get(name=settings.FINANCE_GROUP_NAME)

    if action == 'post_add' and finance_group.pk in pk_set:
        emails = [u.email for u in
                  User.objects.filter(
                      groups__name='Finance',
                      email__isnull=False)]

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
