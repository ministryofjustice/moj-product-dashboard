# -*- coding: utf-8 -*-
import os
from calendar import monthrange
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django import forms

from openpyxl import load_workbook
from xlrd import open_workbook

from dashboard.libs.date_tools import get_workdays
from dashboard.libs.rate_converter import last_date_in_month

from .constants import COST_TYPES
from .models import Person, Rate, Project, PersonCost
from .widgets import MonthYearWidget


PAYROLL_COSTS = [
    'ASLC',
    'A/L Sacrifice',
    'Special Bonus',
    'Temp.Promo.',
    'Misc.Allow.',
    'FTE',
    'Bike Sal',
    'T & S paid with Sal',
    'O/time',
    'ERNIC',
]


def year_range(backward=0, forward=10):
    this_year = date.today().year
    return range(this_year-backward, this_year+forward)


class PayrollUploadForm(forms.Form):
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
                staff_number=data['Staff'],
            )
        except Person.DoesNotExist:
            pass

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
        workbook = open_workbook(
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
                    day_rate = Decimal(data['Salary']) / get_workdays(
                        start, start + relativedelta(day=31))
                    staff_number = int(data['Staff'])

                    additional = {}
                    for header in PAYROLL_COSTS:
                        if Decimal(data[header]) != 0:
                            additional[header] = Decimal(data[header])

                    if Decimal('Write Offs') != 0:
                        additional['Write Offs'] = -Decimal(data['Write Offs'])

                    payroll.append({
                        'person': person,
                        'rate': day_rate,
                        'start': start,
                        'end': last_date_in_month(start),
                        'staff_number': staff_number,
                        'additional': additional
                    })

        return payroll

    def save(self):
        for pay in self.cleaned_data['payroll_file']:
            person = pay['person']
            rate, created = Rate.objects.get_or_create(
                person=person,
                start_date=pay['start'],
                defaults=dict(rate=pay['rate'],)
            )

            if not created:
                rate.rate = pay['rate']
                rate.save()

            if not person.staff_number:
                person.staff_number = pay['staff_number']
                person.save()

            for name, cost in pay['additional'].items():
                additional, created = PersonCost.objects.get_or_create(
                    person=person,
                    start_date=pay['start'],
                    end_date=pay['end'],
                    type=COST_TYPES.MONTHLY,
                    name=name
                )
                additional.cost = cost
                additional.save()


class ExportForm(forms.Form):
    template = 'xls/Journal_Template.xltm'

    date = forms.DateField(required=True, widget=MonthYearWidget(
        years=year_range(backward=4, forward=3)
    ))
    project = forms.ModelChoiceField(
        queryset=Project.objects.visible(),
        required=True)

    def export(self):
        wb = load_workbook(self._get_template(), keep_vba=True)
        self.write(wb)
        return wb

    def _get_template(self):
        return os.path.join(
            os.path.realpath(os.path.dirname(__file__)),
            'templates',
            self.template
        )

    def write(self, workbook, ws=None):
        if ws is None:
            ws = workbook.get_active_sheet()
        project = self.cleaned_data['project']
        date = self.cleaned_data['date']
        month = date.strftime('%B \'%y')
        period_start = date if date.month < 4 else \
            date.replace(year=date.year + 1)
        period_end = period_start.replace(year=date.year + 1)
        period = '%s-%s' % (period_start.strftime('%y'),
                            period_end.strftime('%y'))

        last_business_day = monthrange(date.year, date.month)[1]

        start_date = date
        end_date = date.replace(day=last_business_day)

        ws.cell(row=161, column=7).value = project.hr_id
        ws.cell(row=162, column=7).value = project.hr_id
        ws.cell(row=163, column=7).value = project.hr_id
        ws.cell(row=164, column=7).value = project.hr_id
        ws.cell(row=165, column=7).value = project.hr_id

        ws.cell(row=161, column=10).value = \
            '%s - %s Share of DS Agency Costs %s' % (project.name, project.client.name, month)
        ws.cell(row=162, column=10).value = \
            '%s - %s Share of DS Salary Costs %s' % (project.name, project.client.name, month)
        ws.cell(row=163, column=10).value = \
            '%s - %s Share of DS Allce Costs %s' % (project.name, project.client.name, month)
        ws.cell(row=164, column=10).value = \
            '%s - %s Share of DS ERNIC Costs %s' % (project.name, project.client.name, month)
        ws.cell(row=165, column=10).value = \
            '%s - %s Share of DS ASLC Costs %s' % (project.name, project.client.name, month)
        ws.cell(row=166, column=10).value = \
            '%s - %s Share of DS Resource Costs %s' % (project.name, project.client.name, month)

        ws.cell(row=11, column=9).value = '%s%s' % (last_business_day,
                                                    date.strftime('/%m/%Y'))
        ws.cell(row=12, column=9).value = '%s%s' % (date.strftime('%B'),
                                                    period)
        ws.cell(row=13, column=9).value = 'MA100_LW_%s_13' % \
                                          date.strftime('%d%m%y')

        ws.cell(row=14, column=9).value = '%s - %s Share of DS Costs %s' % \
                                          (project.name, project.client.name,
                                           month)

        ws.cell(row=161, column=9).value = project.people_costs(start_date, end_date, contractor_only=True)
        ws.cell(row=162, column=9).value = project.people_costs(start_date, end_date, non_contractor_only=True)
        ws.cell(row=163, column=9).value = 10
        ws.cell(row=164, column=9).value = 10
        ws.cell(row=165, column=9).value = 10
        ws.cell(row=166, column=9).value = 10


class AdjustmentExportForm(ExportForm):

    def write(self, workbook, ws=None):
        ws = workbook.get_active_sheet()
        super(AdjustmentExportForm, self).write(workbook, ws=ws)
        ws.cell(row=8, column=9).value = 'Intercompany Transfer'


class IntercompanyExportForm(ExportForm):

    def write(self, workbook, ws=None):
        ws = workbook.get_active_sheet()
        super(IntercompanyExportForm, self).write(workbook, ws=ws)
        ws.cell(row=8, column=9).value = 'Intercompany Transfer'
