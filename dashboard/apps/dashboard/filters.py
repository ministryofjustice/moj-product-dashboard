# -*- coding: utf-8 -*-
from django.contrib import admin


class DefaultNoneChoicesFilter(admin.SimpleListFilter):
    def choices(self, cl):
        for lookup, title in self.lookup_choices:  # pragma: no cover
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def lookups(self, request, model_admin):
        return (
            ('all', 'All'),
            (None, 'Yes'),
            ('no', 'No'),
        )


class IsCivilServantFilter(admin.SimpleListFilter):
    """
    this filter shows labels of civil servant or contractor
    instead of boolean flags
    """
    title = 'civil servant | contractor'
    parameter_name = 'is_civil_servant'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Civil Servant'),
            ('no', 'Contractor'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_contractor=False)
        elif self.value() == 'no':
            return queryset.filter(is_contractor=True)
        else:
            return queryset


class IsCurrentStaffFilter(DefaultNoneChoicesFilter):
    """
    this filter shows `is_current=True` by default
    """
    title = 'is current staff?'
    parameter_name = 'is_current_staff'

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(is_current=True)
        elif self.value() == 'no':
            return queryset.filter(is_current=False)
        else:
            return queryset


class HasRateFilter(admin.SimpleListFilter):
    """
    this filter shows people either with rate info or not
    """
    title = 'has rate?'
    parameter_name = 'has_rate'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() is 'yes':
            return queryset.exclude(rates=None)
        elif self.value() == 'no':
            return queryset.filter(rates=None)
        else:
            return queryset


class IsVisibleFilter(DefaultNoneChoicesFilter):
    """
    this filter shows `visible=True` by default
    """
    title = 'is visible?'
    parameter_name = 'visible'

    def queryset(self, request, queryset):
        if self.value() in [None, 'yes']:
            return queryset.filter(visible=True)
        elif self.value() == 'no':
            return queryset.filter(visible=False)
        else:
            return queryset
