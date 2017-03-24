# From: https://djangosnippets.org/snippets/1688/
import datetime
import re

from django.forms.widgets import Widget, TextInput
from django.utils.safestring import mark_safe

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class DateWidget(Widget):
    day_field = '%s_day'
    month_field = '%s_month'
    year_field = '%s_year'

    def render(self, name, value, attrs=None):
        def str_format(i):
            return "%02d" % int(i)

        try:
            year_val, month_val, day_val = map(str_format, [value.year, value.month, value.day])
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, str):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = map(str_format, match.groups())

        output = []

        if 'id' in self.attrs:  # pragma: no cover
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        local_attrs = self.build_attrs(id=self.month_field % id_)
        local_attrs.update({
            'size': 3,
            'maxlength': 2,
            'placeholder': 'MM',
            'autocomplete': 'off',
            'class': 'form-control date-range-two',
        })

        s = TextInput()
        day_html = s.render(self.day_field % name, day_val, local_attrs)
        output.append(day_html)

        s = TextInput()
        month_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(month_html)

        local_attrs['id'] = self.year_field % id_
        local_attrs.update({
            'size': 5,
            'maxlength': 4,
            'placeholder': 'YYYY',
            'class': 'form-control date-range-four',
        })

        s = TextInput()
        year_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(year_html)

        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == "0":  # pragma: no cover
            return None
        if y and m and d:  # pragma: no cover
            try:
                return datetime.date(int(y), int(m), int(d)).strftime('%Y-%m-%d')
            except ValueError:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)


class DateRangeWidget(Widget):
    from_field = '%s_from'
    to_field = '%s_to'

    def render(self, name, value, attrs=None):
        try:
            from_val, to_val = value.split(':')
        except (TypeError, ValueError, AttributeError) as e:
            from_val = to_val = None

        output = []

        f = DateWidget()
        from_html = f.render(self.from_field % name, from_val, attrs)
        output.append(from_html)

        output.append('&nbsp;to&nbsp;')

        t = DateWidget()
        to_html = t.render(self.to_field % name, to_val, attrs)
        output.append(to_html)

        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        f = DateWidget().value_from_datadict(data, files, self.from_field % name)
        t = DateWidget().value_from_datadict(data, files, self.to_field % name)
        if f and t:  # pragma: no cover
            return '%s:%s' % (f, t)
        return data.get(name, None)
