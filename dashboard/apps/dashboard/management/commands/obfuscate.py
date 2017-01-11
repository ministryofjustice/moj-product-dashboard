# -*- coding: utf-8 -*-
from django.core.management import BaseCommand

from dashboard_auth.models import DashboardUser

from ...models import (Person, PersonCost, Rate, Task, Product, Cost, Saving,
                       Budget, ProductStatus, ProductGroupStatus,
                       ProductGroup, Link, Area)


class Command(BaseCommand):
    help = 'Obfuscate naming data and optionally delete all but one ' \
           'project and all but one person'

    def add_arguments(self, parser):
        parser.add_argument('-pe', '--person', type=int)
        parser.add_argument('-pr', '--product', type=int)

    def delete_other_people(self, other_than):
        Person.objects.exclude(pk=other_than).delete()
        Rate.objects.exclude(person_id=other_than).delete()
        PersonCost.objects.exclude(person_id=other_than).delete()
        Task.objects.exclude(person_id=other_than).delete()

    def delete_other_products(self, other_than):
        Product.objects.exclude(pk=other_than).delete()
        Task.objects.exclude(product_id=other_than).delete()
        Cost.objects.exclude(product_id=other_than).delete()
        Saving.objects.exclude(product_id=other_than).delete()
        Budget.objects.exclude(product_id=other_than).delete()
        ProductStatus.objects.exclude(product_id=other_than).delete()
        ProductGroupStatus.objects.all().delete()
        ProductGroup.objects.all().delete()
        Link.objects.exclude(product_id=other_than).delete()
        Area.objects.filter(products__isnull=True).delete()

    def handle(self, *args, **options):  # noqa
        """
        deletes all except person and product and obfuscates naming data
        """
        DashboardUser.objects.all().delete()

        if options.get('person'):
            self.delete_other_people(options.get('person'))
        if options.get('product'):
            self.delete_other_products(options.get('product'))

        # Then Obfuscate
        for p in Person.objects.all():
            p.name = 'Fake Name'
            p.float_id = str(p.pk)
            p.staff_number = p.pk
            p.email = 'fake@email.com'
            p.avatar = None
            p.job_title = None
            p.raw_data = None
            p.save()

        for p in PersonCost.objects.all():
            p.name = None
            p.note = None
            p.save()

        for t in Task.objects.all():
            t.name = None
            t.raw_data = None
            t.float_id = str(t.pk)
            t.save()

        for p in Product.objects.all():
            p.name = 'Fake Product Name'
            p.description = None
            p.product_manager = None
            p.delivery_manager = None
            p.float_id = str(p.pk)
            p.hr_id = None
            p.raw_data = None
            p.save()

        for c in Cost.objects.all():
            c.name = None
            c.note = None
            c.save()

        for s in Saving.objects.all():
            s.name = None
            s.note = None
            s.save()

        for b in Budget.objects.all():
            b.name = None
            b.note = None
            b.save()

        for p in ProductStatus.objects.all():
            p.reason = None
            p.save()

        for l in Link.objects.all():
            l.name = None
            l.url = 'http://url.com'
            l.note = None
            l.save()

        for a in Area.objects.all():
            a.name = 'Fake Area Name'
            a.float_id = str(a.pk)
            a.raw_data = None
            a.save()
