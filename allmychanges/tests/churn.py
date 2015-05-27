# coding: utf-8
from datetime import date
from nose.tools import eq_

from allmychanges.churn import calculate_churns, fill_churn_sequence
from allmychanges.utils import map_days


def test_churn_resurrect():
    history = [date(2014, 3, 1),  # registered
               date(2014, 3, 2),  # active
               date(2014, 3, 7),  # still active
                                  # become churned at 2014-04-04 (28 inactive days)
               date(2014, 4, 15)] # come back after long period (resurrected)
                                  # and we missed hum 2014-05-13

    expected = [(date(2014, 3, 1), 'registered'),
                (date(2014, 4, 4), 'churned'),
                (date(2014, 4, 15), 'resurrected'),
                (date(2014, 5, 13), 'churned')]

    result = calculate_churns(history)
    eq_(expected, result)


def fill(from_date, to_date, state):
    return list(map_days(from_date,
                         to_date,
                         lambda date: (date, state)))


def test_churn_sequence_filling():
    sequence = [(date(2014, 3, 1), 'registered')]
    today = date(2014, 3, 3)
    expected = fill(date(2014, 3, 1), date(2014, 3, 3), 'registered')
    result = fill_churn_sequence(sequence, today)
    eq_(expected, result)


def test_churn_sequence_filling_complex():
    sequence = [(date(2014, 3, 1), 'registered'),
                (date(2014, 4, 4), 'churned'),
                (date(2014, 4, 15), 'resurrected'),
                (date(2014, 5, 13), 'churned')]
    today = date(2014, 5, 15)
    expected = fill(date(2014, 3, 1), date(2014, 4, 4), 'registered') + \
               fill(date(2014, 4, 4), date(2014, 4, 15), 'churned') + \
               fill(date(2014, 4, 15), date(2014, 5, 13), 'resurrected') + \
               fill(date(2014, 5, 13), today, 'churned')
    result = fill_churn_sequence(sequence, today)
    eq_(expected, result)
