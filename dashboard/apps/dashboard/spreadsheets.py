# -*- coding: utf-8 -*-
from datetime import date
import re

from openpyxl.styles import Style, Font
from openpyxl.workbook import Workbook

from dashboard.libs.date_tools import parse_date


class Products:

    date_style = Style(number_format='DD/MM/YYYY')
    bold_font = Font(bold=True)
    bold_style = Style(font=bold_font)
    currency_style = Style(number_format='£#,##0.00')

    def __init__(self, products):
        self.workbook = Workbook()
        self.fill_main_sheet(self.workbook.active, products)
        if len(products) == 1:
            # only create monthly spend sheet when there is one product
            self.fill_monthly_spend_sheet(self.workbook.create_sheet(), products[0])

    @staticmethod
    def format(value):
        if isinstance(value, date):
            return value.strftime('%d/%m/%Y')
        return value

    @staticmethod
    def kwarg_vals(kwargs):
        vals = []
        for k, v in kwargs.items():
            if k == 'year':
                v = '%s-%s' % (str(v)[2:], str(v + 1)[2:])
            vals.append(v)
        return vals

    def fill_main_sheet(self, sheet, products):
        year = date.today().year

        fields = (
            # (header, style, method kwargs)
            ('Id', None, {}),
            ('Name', None, {}),
            ('Description', None, {}),
            ('Area name', None, {}),
            ('Discovery date', self.date_style, {}),
            ('Alpha_date', self.date_style, {}),
            ('Beta date', self.date_style, {}),
            ('Live date', self.date_style, {}),
            ('End date', self.date_style, {}),
            ('Discovery fte', None, {}),
            ('Alpha fte', None, {}),
            ('Beta fte', None, {}),
            ('Live fte', None, {}),
            ('Final budget', self.currency_style, {}),
            ('Cost of discovery', self.currency_style, {}),
            ('Cost of alpha', self.currency_style, {}),
            ('Cost of beta', self.currency_style, {}),
            ('Cost in FY', self.currency_style, {'year': year - 2}),
            ('Cost in FY', self.currency_style, {'year': year - 1}),
            ('Cost in FY', self.currency_style, {'year': year}),
            ('Cost in FY', self.currency_style, {'year': year + 1}),
            ('Cost of sustaining', self.currency_style, {}),
            ('Total recurring costs', self.currency_style, {}),
            ('Savings enabled', self.currency_style, {}),
            ('Visible', None, {}),
        )
        sheet.title = 'Products info'
        for col, (f, style, kwargs) in enumerate(fields):
            cell = sheet.cell(row=1, column=col + 1)
            cell.style = self.bold_style
            cell.value = '{} {}'.format(f, ' '.join(str(k) for k in self.kwarg_vals(kwargs)))
        sheet.freeze_panes = sheet['A2']

        for row, product in enumerate(products):
            for col, (f, style, kwargs) in enumerate(fields):
                val = getattr(product, re.sub('[^0-9a-zA-Z]+', '_', f).lower())
                if callable(val):
                    val = val(**kwargs)
                val = self.format(val)
                cell = sheet.cell(row=row + 2, column=col + 1)
                if style:
                    cell.style = style
                cell.value = val

    def fill_monthly_spend_sheet(self, sheet, product):
        sheet.title = 'Monthly spend'
        time_frames = product.profile(freq='MS')['financial']['time_frames']
        row_names = ['budget', 'savings', 'total', 'remaining']
        for ind, name in enumerate(row_names):
            row_header = sheet.cell(row=ind + 2, column=1)
            row_header.style = self.bold_style
            row_header.value = name

        for ind, time_frame in enumerate(sorted(time_frames.keys())):
            col_header = sheet.cell(row=1, column=ind + 2)
            col_header.style = self.bold_style
            col_header.value = parse_date(time_frame.split('~')[0]).strftime('%b %y')

            for row_ind, row_name in enumerate(row_names):
                cell = sheet.cell(row=row_ind + 2, column=ind + 2)
                cell.style = self.currency_style
                cell.value = round(time_frames[time_frame][row_name], 0)
