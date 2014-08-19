# -*- coding: utf-8 -*-
import logging
import datetime
import time

from django.db.models import Count
from django.db import transaction
from django.utils import timezone

from allmychanges.utils import (
    count,
    count_time,
    update_changelog,
    UpdateError)

from twiggy_goodies.django_rq import job
from twiggy_goodies.threading import log


from functools import wraps
from django_rq.queues import get_queue
import inspect


def get_func_name(func):
    """Helper to get same name for the job function as rq does.
    """
    if inspect.ismethod(func):
        return func.__name__
    elif inspect.isfunction(func) or inspect.isbuiltin(func):
        return '%s.%s' % (func.__module__, func.__name__)

    raise RuntimeError('unable to get func name')


def singletone(func):
    """A decorator for rq's `delay` method which
    ensures there is no a job with same name
    and arguments already in the queue.
    """
    orig_delay = func.delay
    func_name = get_func_name(func)

    @wraps(func.delay)
    def wrapper(*args, **kwargs):
        queue = get_queue('default')
        jobs = queue.get_jobs()

        already_in_the_queue = False
        for j in jobs:
            if j.func_name == func_name \
               and j.args == args \
               and j.kwargs == kwargs:
                already_in_the_queue = True
                break
        if not already_in_the_queue:
            return orig_delay(*args, **kwargs)

    func.delay = wrapper
    return func


@singletone
@job
@transaction.commit_on_success
def update_repo(repo_id):
    try:
        with count_time('task.update_repo.time'):
            from .models import Repo
            repo = Repo.objects.get(pk=repo_id)
            repo._update()

    except Exception:
        logging.getLogger('tasks') \
               .exception('Unhandler error in update_repo worker')
        raise


@singletone
@job
@transaction.commit_on_success
def schedule_updates(reschedule=False, packages=[]):
    from .models import Changelog

    stale_changelogs = Changelog.objects.filter(
        processing_started_at__lt=timezone.now() - datetime.timedelta(0, 60 * 60))

    num_stale = len(stale_changelogs)
    
    if num_stale > 0:
        log.info('{0} stale changelogs were found', num_stale)
        count('task.schedule_updates.stale.count', num_stale)
        stale_changelogs.update(processing_started_at=None)

    if packages:
        changelogs = Changelog.objects.filter(packages__name__in=packages).distinct()
    else:
        changelogs = Changelog.objects.annotate(Count('packages')).filter(packages__count__gt=0)

    if not reschedule:
        changelogs = changelogs.filter(next_update_at__lte=timezone.now())

    num_changelogs = len(changelogs)
    count('task.schedule_updates.scheduling.count', num_changelogs)
    log.info('Rescheduling {0} changelogs update'.format(num_changelogs))

    for changelog in changelogs:
        update_changelog_task.delay(changelog.source)

    delete_empty_changelogs.delay()


@singletone
@job
@transaction.commit_on_success
def delete_empty_changelogs():
    from .models import Changelog
    Changelog.objects.annotate(Count('packages'), Count('versions')) \
                     .filter(packages__count=0, versions__count=0) \
                     .delete()


@singletone
@job('default', timeout=600)
@transaction.commit_on_success
def update_changelog_task(source):
    with log.fields(source=source):
        log.info('Starting task')
        from .models import Changelog

        changelog = None
        tries = 10
        while changelog is None and tries > 0:
            try:
                changelog = Changelog.objects.get(source=source)
            except Changelog.DoesNotExist:
                log.error('Changelog with source={source} not found'.format(
                    **locals()))
                time.sleep(1)
                # we make commit to refresh transaction state and to
                # look if changelog object appeared in the database
                transaction.commit()
                tries -= 1

        assert changelog is not None, 'Changelog with source={source} not found'.format(
                    **locals())

        with log.fields(packages=u', '.join(map(unicode, changelog.packages.all()))):
            log.info('processing changelog')

        if changelog.processing_started_at is not None:
            log.info('somebody already processing this changelog')
            return

        try:
            changelog.problem = None
            changelog.processing_started_at = timezone.now()
            changelog.save()

            update_changelog(changelog)
            # TODO: create more complext algorithm to calculate this time
            changelog.next_update_at = timezone.now() + datetime.timedelta(0, 60 * 60)
            changelog.last_update_took = (timezone.now() - changelog.processing_started_at).seconds
        except UpdateError as e:
            changelog.problem = ', '.join(e.args)
        except Exception as e:
            changelog.problem = unicode(e)
        finally:
            if changelog.problem is not None:
                log.warning('Unable to update changelog with source {0}'.format(source))
                next_update_if_error = timezone.now() + datetime.timedelta(0, 1 * 60 * 60)
                changelog.next_update_at = next_update_if_error

            changelog.processing_started_at = None
            changelog.save()


@job
def raise_exception():
    1/0

