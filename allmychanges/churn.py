import arrow
import datetime

from itertools import groupby

from django.db import connection
from allmychanges.utils import map_days, map_pairs
from allmychanges.models import ACTIVE_USER_ACTIONS


def calculate_churns(history, churn_period=28, today=None):
    """Accepts a sequence of dates when user have had some activity
    and returns sequense of pairs (date, action) where action
    could be 'registered', 'churned', 'resurrected'.
    """
    result = []
    if history:
        def add_churn(dt):
            churn_date = arrow.get(from_date)
            churn_date = churn_date.replace(days=churn_period)
            result.append((churn_date.date(),
                           'churned'))
        def add_resurrect(dt):
            result.append((dt, 'resurrected'))

        to_date = from_date = history[0]
        tail = history[1:]
        result.append((from_date, 'registered'))
        while tail:
            to_date = tail[0]
            delta = to_date - from_date
            if delta.days > churn_period:
                add_churn(from_date)
                add_resurrect(to_date)
            from_date = to_date
            tail = tail[1:]

        if today is None:
            today = datetime.date.today()
            delta = today - to_date
            if delta.days > churn_period:
                # if user churned and didn't return yet
                add_churn(from_date)
    return result


def _fill(from_date, to_date, state):
    return list(map_days(from_date,
                         to_date,
                         lambda date: (date, state)))


def fill_churn_sequence(sequence, today=None):
    """Each curn sequence's item is a tuple: (date, 'state')
    Returns a list of (date, 'state') items which cover every day.
    """
    if today is None:
        today = datetime.date.today()
    sequence = sequence + [(today, '')]
    return sum(map_pairs(sequence,
                         lambda from_item, to_item:
                         _fill(from_item[0], to_item[0], from_item[1])),
               [])


def get_user_actions_heatmap(user, only_active=True):
    h = user.history_log.all()
    if only_active:
        h = h.filter(action__in=ACTIVE_USER_ACTIONS)

    grouped = groupby(h, lambda item: item.created_at.date())
    count = lambda iterable: sum(1 for item in iterable)
    grouped = dict((date, count(items)) for date, items in grouped)
    return grouped


def get_graph_data(from_date, to_date):
    cursor = connection.cursor()

    def get_data(state):
        cursor.execute('SELECT date, count(state) '
                       'FROM allmychanges_userstatehistory '
                       'WHERE state=%s GROUP BY date',
                       state)
        data = dict(cursor.fetchall())
        return list(map_days(from_date, to_date, data.get))

    labels = list(map_days(from_date, to_date, lambda day: day))
    data = tuple(dict(data=get_data(state), name=state)
                 for state in ('registered', 'churned', 'resurrected'))
    return labels, data
