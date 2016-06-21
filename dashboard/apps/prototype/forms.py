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
    payroll_file = forms.FileField(required=True)
    date = forms.DateField(required=True, widget=MonthYearWidget(
        years=year_range(backward=4, forward=3)
    ))

    @property
    def month(self):
        return self.cleaned_data['date'].strftime('%Y-%m')

    def process_upload(self):
        start = self.cleaned_data['date']
        workbook = xlrd.open_workbook(
            file_contents=self.cleaned_data['payroll_file'].read())

        worksheet = workbook.sheet_by_index(0)

        headers = worksheet.row_values(1)
        for row in range(2, worksheet.nrows):
            row_data = worksheet.row_values(row)
            if row_data[0]:
                data = dict(zip(headers, row_data))
                try:
                    person = Person.objects.get(
                        name__icontains=data.get('Surname'))
                except Person.DoesNotExist:
                    self.add_error(
                        None,
                        'ERROR ROW %s: Person not found with Surname "%s"' %
                        (row, data.get('Surname')))
                except Person.MultipleObjectsReturned:
                    self.add_error(
                        None,
                        'ERROR ROW %s: Multiple people found with Surname "%s"' %
                        (row, data.get('Surname')))
                else:
                    day_rate = Decimal(data['Total']) / get_workdays(
                        start, start + relativedelta(day=31))

                    rate = Rate.objects.create(
                        rate=day_rate,
                        person=person,
                        start_date=start,
                    )
            else:
                break
