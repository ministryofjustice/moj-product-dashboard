# -*- coding: utf-8 -*-
from datetime import date

from openpyxl.styles import Style, Font
from openpyxl.workbook import Workbook

from dashboard.libs.date_tools import parse_date


class Products:

    date_style = Style(number_format='DD/MM/YYYY')
    header_style = Style(font=Font(bold=True))
    currency_style = Style(number_format='£#,##0.00')

    def __init__(self, products):
        self.workbook = Workbook()
        self.fill_main_sheet(self.workbook.active, products)
        # create the monthly spend sheet when there is one product.
        # there is no use case for monthly spend sheet for multiple
        # products. if it's needed, column alignment needs to be
        # implemented.
        if len(products) == 1:
            self.fill_monthly_spend_sheet(self.workbook.create_sheet(), products[0])

    def fill_product_info(self, product, sheet, row, include_header=False):

        fields = [
            # (header, style, value)
            ('Id', None, product.id),
            ('Name', None, product.name),
            ('Description', None, product.description),
            ('Area name', None, product.area_name),
            ('Discovery date', self.date_style, product.discovery_date),
            ('Alpha_date', self.date_style, product.alpha_date),
            ('Beta date', self.date_style, product.beta_date),
            ('Live date', self.date_style, product.live_date),
            ('End date', self.date_style, product.end_date),
            ('Discovery fte', None, product.discovery_fte),
            ('Alpha fte', None, product.alpha_fte),
            ('Beta fte', None, product.beta_fte),
            ('Live fte', None, product.live_fte),
            ('Final budget', self.currency_style, product.final_budget),
            ('Cost of discovery', self.currency_style, product.cost_of_alpha),
            ('Cost of alpha', self.currency_style, product.cost_of_alpha),
            ('Cost of beta', self.currency_style, product.cost_of_beta)
        ]

        def _financial_year_col(year):
            header = 'Cost in FY {}-{}'.format(str(year)[2:], str(year + 1)[2:])
            return header, self.currency_style, product.cost_in_fy(year)

        fields += [
            _financial_year_col(date.today().year + offset)
            for offset in range(-2, 2)
        ]

        fields += [
            ('Cost of sustaining', self.currency_style, product.cost_of_sustaining),
            ('Total recurring costs', self.currency_style, product.total_recurring_costs),
            ('Savings enabled', self.currency_style, product.savings_enabled),
            ('Visible', None, product.visible),
        ]

        for idx, (header, style, value) in enumerate(fields):
            column = idx + 1
            if include_header:
                header_cell = sheet.cell(row=row, column=column)
                header_cell.style = self.header_style
                header_cell.value = header
                body_cell = sheet.cell(row=row + 1, column=column)
            else:
                body_cell = sheet.cell(row=row, column=column)
            body_cell.value = value
            if style:
                body_cell.style = style

    def fill_main_sheet(self, sheet, products):
        sheet.title = 'Products info'
        # set the freeze_panes attribute to 'A2',
        # row 1 i.e. header, will always be viewable,
        # no matter where the user scrolls in the spreadsheet
        sheet.freeze_panes = 'A2'

        # fill first product together with headers
        self.fill_product_info(products[0], sheet, 1, include_header=True)
        row = 3
        for product in products[1:]:
            self.fill_product_info(product, sheet, row)
            row += 1

    def fill_monthly_spend_sheet(self, sheet, product):
        sheet.title = 'Monthly spend'
        time_frames = product.profile(freq='MS')['financial']['time_frames']
        row_names = ['budget', 'savings', 'total', 'remaining']
        for idx, name in enumerate(row_names):
            row_header = sheet.cell(row=idx + 2, column=1)
            row_header.style = self.header_style
            row_header.value = name

        for idx, time_frame in enumerate(sorted(time_frames.keys())):
            column = idx + 2
            col_header = sheet.cell(row=1, column=column)
            col_header.style = self.header_style
            col_header.value = parse_date(time_frame.split('~')[0]).strftime('%b %y')

            for idx, row_name in enumerate(row_names):
                cell = sheet.cell(row=idx + 2, column=column)
                cell.style = self.currency_style
                cell.value = round(time_frames[time_frame][row_name], 0)
