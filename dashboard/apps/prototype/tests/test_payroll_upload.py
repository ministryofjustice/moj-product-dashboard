# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from os.path import dirname, abspath, join

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

from model_mommy import mommy
import pytest

from ..forms import PayrollUploadForm
from ..models import Person


@pytest.mark.django_db
def test_valid_upload_form():
    p1 = mommy.make(Person, name='X Surname1', is_contractor=False)
    p2 = mommy.make(Person, name='B Surname2', is_contractor=False)
    p3 = mommy.make(Person, name='C Surname3', is_contractor=False)
    mommy.make(Person, name='C Surname3', is_contractor=True)

    fb = open(abspath(join(dirname(__file__), 'data/payroll_test.xls')), 'rb')
    form = PayrollUploadForm(
        data={'date': date(2016, 1, 1)},
        files=MultiValueDict(
            {'payroll_file': [SimpleUploadedFile(fb.name, fb.read())]}
        ),
    )

    assert form.is_valid() is True
    assert form.cleaned_data['date'] == date(2016, 1, 1)
    assert form.cleaned_data['payroll_file'] == [{'person': p1,
                                                  'rate': Decimal('0.2'),
                                                  'start': date(2016, 1, 1)},
                                                 {'person': p2,
                                                  'rate': Decimal('0.2'),
                                                  'start': date(2016, 1, 1)},
                                                 {'person': p3,
                                                  'rate': Decimal('0.2'),
                                                  'start': date(2016, 1, 1)}]
    assert form.errors == {}
    assert form.month == '2016-01'
    assert form.save() is None
    assert form.save() is None


@pytest.mark.django_db
def test_invalid_upload_form():
    mommy.make(Person, name='AD Surname1', is_contractor=False)
    mommy.make(Person, name='AB Surname1', is_contractor=False)
    mommy.make(Person, name='B Surname2', is_contractor=False)
    mommy.make(Person, name='X Surname3', is_contractor=False)
    mommy.make(Person, name='P Surname3', is_contractor=False)

    fb = open(abspath(join(dirname(__file__), 'data/payroll_test.xls')), 'rb')
    form = PayrollUploadForm(
        data={'date': date(2016, 1, 1)},
        files=MultiValueDict(
            {'payroll_file': [SimpleUploadedFile(fb.name, fb.read())]}
        ),
    )

    assert form.is_valid() is False
    assert form.errors == {
        'payroll_file': ['ERROR ROW 7: Multiple Civil Servants found with '
                         'Surname "SURNAME1"',
                         'ERROR ROW 12: Civil Servant not found with Surname '
                         '"SURNAME3" and initials "CN"']
    }
