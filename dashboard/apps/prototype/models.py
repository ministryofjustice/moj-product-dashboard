# -*- coding: utf-8 -*-
from django.db import models


class Person(models.Model):
    float_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    email = models.EmailField()
    roles = models.ManyToManyField('Role', through='PersonRole')

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=32)
    people = models.ManyToManyField('Person', through='PersonRole')
    default_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_contractor = models.BooleanField()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'is_contractor')


class Rate(models.Model):
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    person = models.ForeignKey('Person', related_name='rates')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        if self.end_date:
            return '"{}" @ "{}"/day from "{}" to "{}"'.format(
                self.person, self.amount, self.start_date, self.end_date)
        else:
            return '"{}" @ "{}"/day from "{}"'.format(
                self.person, self.amount, self.start_date)


class PersonRole(models.Model):
    person = models.ForeignKey('Person')
    role = models.ForeignKey('Role')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        if self.end_date:
            return '"{}" "{}" from "{}" to "{}"'.format(
                self.role, self.person, self.start_date, self.end_date)
        else:
            return '"{}" "{}" from "{}"'.format(
                self.role, self.person, self.start_date)


class Client(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=32)
    managers = models.ManyToManyField('Person')
    client = models.ForeignKey('Client', related_name='projects')
    discovery_date = models.DateTimeField(null=True)
    alpha_date = models.DateTimeField(null=True)
    beta_date = models.DateTimeField(null=True)
    live_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=32)
    person = models.ForeignKey('Person', related_name='tasks')
    project = models.ForeignKey('Project', related_name='tasks')
    start_date = models.DateTimeField()
    days = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name
