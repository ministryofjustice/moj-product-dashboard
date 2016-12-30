# -*- coding: utf-8 -*-
from extended_choices import Choices


RAG_TYPES = Choices(
    ('GREEN',  1, 'Green'),
    ('GREENAMBER',   2, 'Green/Amber'),
    ('AMBER',   3, 'Amber'),
    ('AMBERRED', 4, 'Amber/Red'),
    ('RED', 5, 'Red'),
)


COST_TYPES = Choices(
    ('ONE_OFF',  1, 'One off'),
    ('MONTHLY',  2, 'Monthly'),
    ('ANNUALLY',  3, 'Annually'),
)


STATUS_TYPES = Choices(
    ('OK',  1, 'OK'),
    ('AT_RISK',  2, 'At risk'),
    ('IN_TROUBLE',  3, 'In trouble'),
    ('PAUSED',  4, 'Paused'),
)
