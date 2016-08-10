# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from model_mommy import mommy
import pytest
from dashboard.apps.prototype.constants import COST_TYPES

from ..models import Project, Saving


class NewDate(date):
    @classmethod
    def today(cls):
        return cls(2015, 8, 1)


@pytest.mark.django_db
@patch('dashboard.apps.prototype.models.date', NewDate)
def test_monthly_savings_no_start_end():
    project = mommy.make(Project)

    mommy.make(
        Saving,
        project=project,
        start_date=date(2015, 4, 1),
        type=COST_TYPES.MONTHLY,
        cost=Decimal('100')
    )

    savings = project.additional_costs(None, None,
                                       attribute='savings')

    assert savings == Decimal('500')
