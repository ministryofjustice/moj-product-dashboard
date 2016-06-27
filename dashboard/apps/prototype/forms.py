# -*- coding: utf-8 -*-
from datetime import date, datetime, time
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django import forms
from django.utils import timezone

import xlrd

from dashboard.libs.date_tools import get_workdays

from .models import Person, Rate
from .widgets import MonthYearWidget


def year_range(backward=0, forward=10):
    this_year = date.today().year
    return range(this_year-backward, this_year+forward)


class ConvertDateMixin(object):
    def _convert_date(self, d):
        d = datetime.combine(d, time(hour=0, minute=0))
        d = timezone.make_aware(d, timezone.get_current_timezone())
        return d


class PayrollUploadForm(forms.Form, ConvertDateMixin):
    date = forms.DateField(required=True, widget=MonthYearWidget(
        years=year_range(backward=4, forward=3)
    ))
    payroll_file = forms.FileField(required=True)

    @property
    def month(self):
        return self.cleaned_data['date'].strftime('%Y-%m')

    def get_person(self, row, data):
        try:
            return Person.objects.get(
                name__icontains=data.get('Surname'),
                name__startswith=data.get('Init')[0],
                is_contractor=False,
            )
        except Person.DoesNotExist:
            try:
                return Person.objects.get(
                    name__icontains=data.get('Surname'),
                    is_contractor=False,
                )
            except (Person.DoesNotExist, Person.MultipleObjectsReturned):
                pass
            self.add_error(
                'payroll_file',
                'ERROR ROW %s: Civil Servant not found with Surname "%s" '
                'and initials "%s"' %
                (row, data.get('Surname'), data.get('Init')))
        except Person.MultipleObjectsReturned:
            self.add_error(
                'payroll_file',
                'ERROR ROW %s: Multiple Civil Servants found with Surname '
                '"%s"' % (row, data.get('Surname')))

    def clean_payroll_file(self):
        start = self.cleaned_data['date']
        workbook = xlrd.open_workbook(
            file_contents=self.cleaned_data['payroll_file'].read())

        worksheet = workbook.sheet_by_index(0)

        headers = worksheet.row_values(6)

        payroll = []

        for row in range(7, worksheet.nrows):
            row_data = worksheet.row_values(row)
            if row_data[0]:
                data = dict(zip(headers, row_data))
                person = self.get_person(row, data)
                if person:
                    day_rate = Decimal(data['Total']) / get_workdays(
                        start, start + relativedelta(day=31))

                    payroll.append({
                        'person': person,
                        'rate': day_rate,
                        'start': start,
                    })

        return payroll

    def save(self):
        for pay in self.cleaned_data['payroll_file']:
            rate, created = Rate.objects.get_or_create(
                person=pay['person'],
                start_date=pay['start'],
                defaults=dict(rate=pay['rate'],)
            )

            if not created:
                rate.rate = pay['rate']
                rate.save()
