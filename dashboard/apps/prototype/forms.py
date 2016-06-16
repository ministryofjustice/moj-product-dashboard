# -*- coding: utf-8 -*-
from datetime import date, datetime, time

from django import forms
from django.conf import settings
from django.utils import timezone

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

