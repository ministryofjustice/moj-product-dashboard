# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy

from .product import ProductGroup


class Area(models.Model):
    name = models.CharField(max_length=128)
    float_id = models.CharField(max_length=128, unique=True)
    visible = models.BooleanField(default=True)
    manager = models.ForeignKey(
        'Person', related_name='+', verbose_name='service manager', null=True)
    raw_data = JSONField(null=True)

    class Meta:
        verbose_name = ugettext_lazy('service area')

    def __str__(self):
        return self.name

    def profile(self, product_ids=None, start_date=None, end_date=None,
                freq='MS', calculation_start_date=None):
        """
        get the profile of a service area in a time window.
        :param product_ids: a list of product_ids, if the value is not
        specified, get all products.
        :param start_date: start date of time window, a date object
        :param end_date: end date of time window, a date object
        :param freq: an optional parameter to slice the time window into
        sub windows. value of freq should be an offset aliases supported by
        pandas date_range, e.g. MS for month start.
        :param calculation_start_date: date when calculation for people costs
        using tasks and rates start
        :return: a dictionary representing the profile
        """
        product_ids_in_a_group = [
            p.id
            for group in ProductGroup.objects.all()
            for p in group.products.all()
        ]
        products = self.products.visible().exclude(
            id__in=product_ids_in_a_group)
        product_groups = [group for group in ProductGroup.objects.all()
                          if group.area and group.area.id == self.id]
        if product_ids is not None:
            products = products.filter(id__in=product_ids)
        result = {
            'id': self.id,
            'name': self.name
        }
        result['products'] = {
            'product:{}'.format(product.id): product.profile(
                start_date, end_date, freq,
                calculation_start_date=calculation_start_date)
            for product in products
        }
        result['products'].update({
            'product-group:{}'.format(group.id): group.profile(
                start_date, end_date, freq)
            for group in product_groups
        })
        return result
