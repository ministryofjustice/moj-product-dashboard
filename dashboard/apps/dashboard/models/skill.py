# -*- coding: utf-8 -*-
from django.db import models
from django.core import urlresolvers
from django.contrib.contenttypes.models import ContentType


class Skill(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

    @property
    def admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        name = 'admin:{}_{}_change'.format(content_type.app_label,
                                           content_type.model)
        return urlresolvers.reverse(name, args=(self.id,))
