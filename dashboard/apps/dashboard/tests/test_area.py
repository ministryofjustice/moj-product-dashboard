# -*- coding: utf-8 -*-
from model_mommy import mommy
import pytest

from dashboard.apps.prototype.models import Area, Product


@pytest.mark.django_db
def test_area():
    area = mommy.make(Area)
    products = [mommy.make(Product, area=area) for _ in range(10)]
    assert str(area) == area.name
    sorted_pids = sorted([p.id for p in products])
    assert [p.id for p in area.products.order_by('id')] == sorted_pids


@pytest.mark.django_db
def test_area_profile():
    area = mommy.make(Area)
    products = [mommy.make(Product, area=area) for _ in range(10)]
    profile1 = area.profile()
    profile2 = area.profile(product_ids=[p.id for p in products])
    assert profile1 == profile2
