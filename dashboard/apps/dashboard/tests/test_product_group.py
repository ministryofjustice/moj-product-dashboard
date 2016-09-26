from decimal import Decimal

import pytest
from model_mommy import mommy

from dashboard.apps.dashboard.models import ProductGroup, Area
from .test_product import make_product


@pytest.mark.django_db
def test_product_group():
    area1 = mommy.make(Area, name='area1')
    p1 = make_product()
    p2 = make_product()
    p1.area = area1
    p2.area = area1
    p1.save()
    p2.save()

    pg = ProductGroup(name='PG1')
    pg.save()
    pg.products.add(p1)
    pg.products.add(p2)
    assert str(pg) == 'PG1'

    profile = pg.profile(freq='MS')
    financial = {
        '2016-01-01~2016-01-31': {
            'non-contractor': Decimal('2800'),
            'contractor': Decimal('3200'),
            'budget': Decimal('0'),
            'additional': Decimal('0'),
            'savings': Decimal('0'),
            'remaining': Decimal('-6000'),
            'total': Decimal('6000')
        }
    }
    assert profile['financial']['time_frames'] == financial
    assert profile['name'] == 'PG1'
    assert profile['service_area'] == {'id': area1.id, 'name': area1.name}


@pytest.mark.django_db
def test_product_group_area():
    area1 = mommy.make(Area, name='area1')

    p1 = make_product()
    p2 = make_product()
    p1.area = area1
    p2.area = area1
    p1.save()
    p2.save()

    pg = ProductGroup(name='PG1')
    pg.save()
    pg.products.add(p1)
    pg.products.add(p2)

    assert pg.area == area1
    assert [pg.id for pg in p1.product_groups.all()] == [pg.id]
    assert [pg.id for pg in p2.product_groups.all()] == [pg.id]

    area2 = mommy.make(Area, name='area2')
    p2.area = area2
    p2.save()
    assert pg.area is None
