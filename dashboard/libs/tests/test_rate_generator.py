import pytest

from dashboard.libs.rate_generator import get_reference_rate, gen_rates


@pytest.mark.parametrize("job_title, is_contractor, expected", [
    # match the job title 100%
    ('Agile Coach', True, 750),
    ('Agile Coach', False, 750),
    ('Developer', True, 465),
    ('Developer', False, 390),
    ('Web Ops Developer', True, 609),
    ('Web Ops Developer', False, 360),

    # match the job title more than 60%
    ('Python Developer', True, 465),
    ('Ruby Developer', True, 465),
    ('Junior Developer', True, 465),
    ('Senior Developer', True, 465),
    ('Front End Developer', True, 465),
    ('Web Ops', True, 609),
    ('Web Ops Engineer', True, 609),
    ('Web-ops', True, 609),

    # match the job title less than 60%
    ('Common Doorway/Strategy Assistant', False, 375),
    ('Head of Digital Communications', False, 375),
    ('Executive Assistant', False, 375),
])
def test_get_reference_rate(job_title, is_contractor, expected):
    assert get_reference_rate(job_title, is_contractor) == expected


def test_gen_rates():
    rates = gen_rates('2015-01-01', '2017-01-01', '2QS', 450, 500)
    dates = ['2015-01-01', '2015-07-01',
             '2016-01-01', '2016-07-01',
             '2017-01-01']
    assert [d.strftime('%Y-%m-%d') for d in rates.index.date] == dates
    for val in rates.values:
        assert 450 <= val <= 500
