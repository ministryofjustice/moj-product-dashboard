"""
random rate generator
"""
import pandas as pd
from numpy.random import randint
from fuzzywuzzy import process


DEFAULT_RATES = {
    "civil servant": 375,
    "code": "IA",
    "contractor": 487
}

REFERENCE_RATES_BY_TITLE = {
  "Agile Coach": {
    "civil servant": 750,
    "title": "Agile Coach",
    "code": "AC",
    "contractor": 750
  },
  "Service Manager": {
    "civil servant": 480,
    "title": "Service Manager",
    "code": "SM",
    "contractor": 647
  },
  "Content Designer": {
    "civil servant": 360,
    "title": "Content Designer",
    "code": "CON",
    "contractor": 350
  },
  "Business Analyst": {
    "civil servant": 480,
    "title": "Business Analyst",
    "code": "BA",
    "contractor": 480
  },
  "Technical Architect": {
    "civil servant": 480,
    "title": "Technical Architect",
    "code": "TA",
    "contractor": 558
  },
  "Product Manager": {
    "civil servant": 420,
    "title": "Product Manager",
    "code": "PM",
    "contractor": 527
  },
  "Web Ops Developer": {
    "civil servant": 360,
    "title": "Web Ops Developer",
    "code": "WEB OPS",
    "contractor": 609
  },
  "Designer": {
    "civil servant": 360,
    "title": "Designer",
    "code": "DES",
    "contractor": 463
  },
  "Developer": {
    "civil servant": 390,
    "title": "Developer",
    "code": "DEV",
    "contractor": 465
  },
  "User Researcher": {
    "civil servant": 300,
    "title": "User Researcher",
    "code": "UR",
    "contractor": 453
  },
  "Delivery Manager": {
    "civil servant": 360,
    "title": "Delivery Manager",
    "code": "DM",
    "contractor": 533
  }
}


def get_reference_rate(job_title, is_contractor):
    """
    get the reference daily rate based on the job title and whether it is
    for contractor. the function does a fuzzy match between the given
    job title and all the standard titles. if a probability greater than 60
    can be found, use the rate for the title, otherwise use the default rate.
    :param job_title: the job title string
    :param is_contractor: boolean
    :return: daily rate in integer value
    """
    extracts = process.extract(job_title, REFERENCE_RATES_BY_TITLE .keys())
    matched, probability = extracts[0]
    if probability > 60:
        print('matched title: {}, probability: {}'.format(
            matched, probability))
        rates = REFERENCE_RATES_BY_TITLE[matched]
    else:
        print('could not find a matched title')
        rates = DEFAULT_RATES
    if is_contractor:
        return rates['contractor']
    else:
        return rates['civil servant']


def gen_rates(start_date, end_date, freq, min_rate, max_rate):
    """
    generate rates in a date range with a frequency based on a reference rate
    """
    date_range = pd.date_range(start_date, end_date, freq=freq)
    rates = pd.Series(randint(min_rate, max_rate, len(date_range)),
                      index=date_range)
    return rates
