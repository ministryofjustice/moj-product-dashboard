# -*- coding: utf-8 -*-
from model_mommy import mommy
import pytest

from ..admin import IsCivilServantFilter, IsCurrentStaffFilter, PersonAdmin
from ..models import Person


def create_fixtures():
    p1 = mommy.make(Person, name='p1', is_current=True, is_contractor=True)
    p2 = mommy.make(Person, name='p2', is_current=True, is_contractor=False)
    p3 = mommy.make(Person, name='p3', is_current=False, is_contractor=True)
    p4 = mommy.make(Person, name='p4', is_current=False, is_contractor=False)
    return {'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4}


@pytest.mark.parametrize('value,names', [
    ('yes', ['p2', 'p4']),
    ('no',  ['p1', 'p3']),
    (None,  ['p1', 'p2', 'p3', 'p4']),
])
@pytest.mark.django_db
def test_is_civil_servant_filter(value, names):
    create_fixtures()
    filter = IsCivilServantFilter(
        None, {'is_civil_servant': value}, Person, PersonAdmin)
    result = filter.queryset(None, Person.objects.all())
    assert set([p.name for p in result]) == set(names)


@pytest.mark.parametrize('value,names', [
    (None,   ['p1', 'p2']),
    ('no',   ['p3', 'p4']),
    ('all',  ['p1', 'p2', 'p3', 'p4']),
])
@pytest.mark.django_db
def test_is_current_staff_filter(value, names):
    create_fixtures()
    filter = IsCurrentStaffFilter(
        None, {'is_current_staff': value}, Person, PersonAdmin)
    result = filter.queryset(None, Person.objects.all())
    assert set([p.name for p in result]) == set(names)


@pytest.mark.parametrize('key,expected', [
    ('p1', 'Contractor'),
    ('p2', 'Civil Servant'),
    ('p3', 'Contractor'),
    ('p4', 'Civil Servant'),
])
@pytest.mark.django_db
def test_person_admin_contractor_civil_servant(key, expected):
    people = create_fixtures()
    admin = PersonAdmin(Person, None)
    assert admin.contractor_civil_servant(people[key]) == expected
