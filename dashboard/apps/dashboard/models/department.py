# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import JSONField


class Department(models.Model):
    float_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    raw_data = JSONField(null=True)

    def __str__(self):
        return self.name
