# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from django.db import models


class Link(models.Model):
    product = models.ForeignKey('Product', related_name='links')
    name = models.CharField(max_length=150, null=True, blank=True)
    url = models.URLField()
    note = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['url']

    def __str__(self):
        return self.name

    @property
    def type(self):
        hostname = urlparse(self.url).hostname
        return hostname.replace('.', '-')

    def as_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'note': self.note,
            'type': self.type,
        }
