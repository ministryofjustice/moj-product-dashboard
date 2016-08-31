# From: https://djangosnippets.org/snippets/1688/
import datetime
import re

from django.forms.widgets import Widget, TextInput
from django.utils.safestring import mark_safe
from django.conf import settings

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class MonthYearDateWidget(Widget):
    month_field = '%s_month'
    year_field = '%s_year'

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, str):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:  # pragma: no cover
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        local_attrs = self.build_attrs(id=self.month_field % id_)
        local_attrs['size'] = 3
        local_attrs['maxlength'] = 2
        local_attrs['placeholder'] = 'MM'
        local_attrs['autocomplete'] = 'off'

        s = TextInput()
        month_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(month_html)

        local_attrs['id'] = self.year_field % id_
        local_attrs['size'] = 5
        local_attrs['maxlength'] = 4
        local_attrs['placeholder'] = 'YYYY'
        local_attrs['autocomplete'] = 'off'

        s = TextInput()
        year_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(year_html)

        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        if y == m == "0":  # pragma: no cover
            return None
        if y and m:  # pragma: no cover
            try:
                return datetime.date(int(y), int(m), 1).strftime(
                    settings.DATE_INPUT_FORMATS[0])
            except ValueError:
                return '%s-%s-01' % (y, m)
        return data.get(name, None)
