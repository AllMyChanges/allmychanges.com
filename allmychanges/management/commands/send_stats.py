import os
import datetime

from pprint import pprint
from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from django.conf import settings
from allmychanges.utils import graphite_send
from allmychanges.models import Changelog, ChangelogTrack, Version, User, Issue
from django.utils import timezone
from django.db.models import Count


def get_stats_from_file():
    """Gets stats dumped to file '.stats'.
    It has simple format like 'name value' on each line

    Usually .stats file used to store such data as number of
    unittests passed/failed, code metrics and parser quality
    metrics.
    """
    filename = os.path.join(settings.PROJECT_ROOT, '.stats')
    if os.path.exists(filename):
        with open(filename) as f:
            lines = f.readlines()
            stats = [line.split(None, 1) for line in lines]
            stats = {name: float(value) for name, value in stats}
            return stats
    return {}


def get_stats():
    stats = get_stats_from_file()

    from rq.scripts.rqinfo import (setup_default_arguments,
                                   parse_args,
                                   setup_redis, Queue)


    args = parse_args()
    setup_default_arguments(args, {})
    setup_redis(args)
    for queue in Queue.all():
        stats['queue.{0}.jobs'.format(queue.name)] = queue.count


    package_counts = list(User.objects.annotate(Count('packages')))

    zero_packages = [user
                     for user in package_counts
                     if user.packages__count == 0]
    others = [user.packages__count
              for user in package_counts
              if user.packages__count > 0]
    stats['db.peruser-package-count.zero'] = len(zero_packages)
    stats['db.peruser-package-count.min'] = min(others)
    stats['db.peruser-package-count.max'] = max(others)
    stats['db.peruser-package-count.avg'] = sum(others) / len(others)

    stats['db.tracks.count'] = ChangelogTrack.objects.count()
    stats['db.changelogs'] = Changelog.objects.count()

    stats['db.users'] = User.objects.count()
    stats['db.active-users.day'] = User.objects.active_users(1)
    stats['db.active-users.week'] = User.objects.active_users(7)
    stats['db.active-users.month'] = User.objects.active_users(30)
    stats['db.active-users.year'] = User.objects.active_users(365)

    stats['db.versions.v1-vcs'] = Version.objects.filter(code_version='v1', changelog__filename=None).count()
    stats['db.versions.v1'] = Version.objects.filter(code_version='v1').exclude(changelog__filename=None).count()
    stats['db.versions.v2'] = Version.objects.filter(code_version='v2', preview_id=None).count()

    stats['db.versions.v1-unreleased'] = Version.objects.filter(code_version='v1', unreleased=True).exclude(changelog__filename=None).count()
    stats['db.versions.v2-unreleased'] = Version.objects.filter(code_version='v2', unreleased=True).count()
    stats['db.users-with-emails'] = User.objects.exclude(email=None).count()

    now = timezone.now()
    minute_ago = now - datetime.timedelta(0, 60)

    stats['crawler.discovered.v1.count'] = Version.objects.filter(
        code_version='v1',
        discovered_at__gte=minute_ago).count()
    stats['crawler.discovered.v2.count'] = Version.objects.filter(
        code_version='v2',
        discovered_at__gte=minute_ago).count()

    # if package wasn't updated within 10 minutes from planned time
    # it is considered stale
    # because 10 minutes is job timeout and this is means that it will
    # never be updated
    stale_margin = timezone.now() - datetime.timedelta(0, 10 * 60)
    stale = Changelog.objects.only_active().filter(next_update_at__lte=stale_margin)
    stats['crawler.stale.packages.count'] = stale.count()

    next_update_times = stale.values_list('next_update_at', flat=True)
    seconds_behind = sum((stale_margin - time).total_seconds() for time in next_update_times)
    stats['crawler.stale.packages.seconds-behind'] = seconds_behind

    last_updates = Changelog.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(0, 60 * 60)).values_list('last_update_took', flat=True)
    stats['crawler.last_update_took.average'] = float(sum(last_updates)) / len(last_updates) if last_updates else 0

    stats['crawler.paused.packages.count'] = Changelog.objects.exclude(paused_at=None).count()

    opened_issues = Issue.objects.filter(resolved_at=None)
    stats['crawler.issues.by-type.total.count'] = opened_issues.count()

    for typ, cnt in opened_issues.values('type').annotate(cnt=Count('type')).values_list('type', 'cnt'):
        stats['crawler.issues.by-type.{0}.count'.format(typ)] = cnt

    stats['crawler.issues.by-status.total.count'] = Issue.objects.count()
    stats['crawler.issues.by-status.opened.count'] = opened_issues.count()
    stats['crawler.issues.by-status.resolved.count'] = Issue.objects.exclude(resolved_at=None).count()

    stats['crawler.issues.from-robot.count'] = opened_issues.filter(user=None, light_user=None).count()
    stats['crawler.issues.from-human.count'] = opened_issues.exclude(user=None, light_user=None).count()

    stats['test.count'] = 42

    return stats


class Command(LogMixin, BaseCommand):
    help = u"""Send stats to graphite Graphite."""

    def handle(self, *args, **options):
        stats = get_stats()
        if args and args[0] == 'dry':
            pprint(stats)
        else:
            graphite_send(**stats)
