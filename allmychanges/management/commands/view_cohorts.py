import arrow
import tablib

from allmychanges.models import User, ACTIVE_USER_ACTIONS


def get_cohort_for(date):
    return User.objects.filter(date_joined__range=
                               (date.date(), date.replace(months=+1).date()))


def get_cohort_stats(cohort, date):
    stats = []
    today = arrow.utcnow()
    total = float(cohort.count())

    while date < today:
        stats.append(cohort.filter(history_log__action__in=ACTIVE_USER_ACTIONS,
                                   history_log__created_at__range=(
                                       date.date(), date.replace(months=+1).date())) \
                     .distinct().count())
        date = date.replace(months=+1)
    return [item / total if total else 0 for item in stats]


start_date = arrow.get(2014, 1, 1)
dates = arrow.Arrow.range('month', start_date, arrow.utcnow())
cohorts = map(get_cohort_for, dates)

stats = map(get_cohort_stats, cohorts, dates)
stats = [item + [''] * (len(stats[0]) - len(item)) for item in stats]

dataset = tablib.Dataset(*stats, headers=range(1, len(stats[0]) + 1))
dataset.insert_col(0,
                   [dt.humanize()
                    for dt in dates],
                   header='cohort')
dataset.insert_col(1,
                   map(len, cohorts),
                   header='num users')
dataset.csv
