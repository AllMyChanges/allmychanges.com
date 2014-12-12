# -*- coding: utf-8 -*-
import math
import logging
import datetime
import time

from django.db.models import Count
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from allmychanges.utils import (
    count,
    count_time)
from allmychanges.exceptions import UpdateError
from allmychanges.changelog_updater import update_preview_or_changelog

from twiggy_goodies.django_rq import job
from twiggy_goodies.threading import log


from functools import wraps
from django_rq.queues import get_queue
import inspect


if settings.DEBUG_JOBS == True:
    _task_log = []
    _orig_job = job
    def job(func, *args, **kwargs):
        """Dont be afraid, this magic is necessary only for unittests
        to be track all delayed tasks."""
        result = _orig_job(func, *args, **kwargs)

        if callable(func):
            def new_delay(*args, **kwargs):
                _task_log.append((func.__name__, args, kwargs))
                return result.delay(*args, **kwargs)
            result.delay = new_delay
            return result
        else:
            def decorator(func):
                new_func = result(func)
                orig_delay = new_func.delay

                def new_delay(*args, **kwargs):
                    _task_log.append((func.__name__, args, kwargs))
                    return orig_delay(*args, **kwargs)
                new_func.delay = new_delay
                return new_func
            return decorator


def get_func_name(func):
    """Helper to get same name for the job function as rq does.
    """
    if inspect.ismethod(func):
        return func.__name__
    elif inspect.isfunction(func) or inspect.isbuiltin(func):
        return '%s.%s' % (func.__module__, func.__name__)

    raise RuntimeError('unable to get func name')


def singletone(queue='default'):
    def decorator(func):
        """A decorator for rq's `delay` method which
        ensures there is no a job with same name
        and arguments already in the queue.
        """
        orig_delay = func.delay
        func_name = get_func_name(func)

        @wraps(func.delay)
        def wrapper(*args, **kwargs):
            queue_obj = get_queue(queue)
            already_in_the_queue = False

            # if queue is not async, then we don't need
            # to check if job already there
            if queue_obj._async:
                jobs = queue_obj.get_jobs()
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
    return decorator


@singletone()
@job
@transaction.atomic
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


@singletone()
@job
@transaction.atomic
def schedule_updates(reschedule=False, packages=[]):
    from .models import Changelog

    if packages:
        changelogs = Changelog.objects.filter(name__in=packages).distinct()
    else:
        changelogs = Changelog.objects.all()

    if not reschedule:
        changelogs = changelogs.filter(next_update_at__lte=timezone.now())

    num_changelogs = len(changelogs)
    count('task.schedule_updates.scheduling.count', num_changelogs)
    log.info('Rescheduling {0} changelogs update'.format(num_changelogs))

    for changelog in changelogs:
        changelog.schedule_update()



# @singletone()
# @job('default', timeout=600)
# @transaction.atomic
# def update_changelog_task_to_remove(source, preview_id=None):
#     with log.fields(source=source, preview_id=preview_id):
#         log.info('Starting task')
#         from .models import Changelog, Preview

#         changelog = None
#         tries = 10

#         while changelog is None and tries > 0:
#             try:
#                 changelog = Changelog.objects.get(source=source)
#             except Changelog.DoesNotExist:
#                 log.error('Changelog with source={source} not found'.format(
#                     **locals()))
#                 time.sleep(1)
#                 # we make commit to refresh transaction state and to
#                 # look if changelog object appeared in the database
#                 transaction.commit()
#                 tries -= 1

#         assert changelog is not None, 'Changelog with source={source} not found'.format(
#                     **locals())

#         log.info('processing changelog')

#         if preview_id is None:
#             if changelog.processing_started_at is not None:
#                 log.info('somebody already processing this changelog')
#                 return

#         problem = None
#         try:
#             if preview_id is None:
#                 changelog.processing_started_at = timezone.now()
#                 changelog.save()

#             update_changelog(changelog, preview_id=preview_id)

#             if preview_id is None:
#                 changelog.last_update_took = (timezone.now() - changelog.processing_started_at).seconds

#                 hour = 60 * 60
#                 min_update_interval = hour
#                 time_to_next_update = 4 * hour
#                 time_to_next_update = time_to_next_update / math.log(max(math.e,
#                                                                          changelog.trackers.count()))

#                 time_to_next_update = max(min_update_interval,
#                                           time_to_next_update,
#                                           2 * changelog.last_update_took)

#                 changelog.next_update_at = timezone.now() + datetime.timedelta(0, time_to_next_update)
#         except UpdateError as e:
#             problem = ', '.join(e.args)
#             log.trace().error('Unable to update changelog')
#         except Exception as e:
#             problem = unicode(e)
#             log.trace().error('Unable to update changelog')
#         finally:
#             if problem is not None:
#                 log.warning(problem)

#                 if preview_id:
#                     preview = Preview.objects.get(pk=preview_id)
#                     preview.problem = problem
#                     preview.updated_at = timezone.now()
#                     preview.save(update_fields=('problem', 'updated_at'))

#                 else:
#                     changelog.problem = problem

#             if preview_id is None:
#                 next_update_if_error = timezone.now() + datetime.timedelta(0, 1 * 60 * 60)
#                 changelog.next_update_at = next_update_if_error
#                 changelog.processing_started_at = None
#                 changelog.save()
#             else:
#                 preview = Preview.objects.get(pk=preview_id)
#                 preview.updated_at = timezone.now()
#                 preview.save(update_fields=('updated_at',))

#             log.info('Task done')


@singletone('preview')
@job('preview', timeout=600)
@transaction.atomic
def update_preview_task(preview_id):
    with log.fields(preview_id=preview_id):
        log.info('Starting task')
        try:
            from .models import Preview
            preview = Preview.objects.get(pk=preview_id)
            update_preview_or_changelog(preview)
        finally:
            log.info('Task done')


@singletone()
@job('default', timeout=600)
@transaction.atomic
def update_changelog_task(source):
    with log.fields(source=source):
        log.info('Starting task')
        processing_started_at = timezone.now()
        error = False

        try:
            from .models import Changelog
            changelog = Changelog.objects.get(source=source)
            update_preview_or_changelog(changelog)

            changelog.last_update_took = (timezone.now() - processing_started_at).seconds
            changelog.next_update_at = changelog.calc_next_update()
            changelog.save()
        except Exception:
            log.trace().error('Error during changelog update')
            error = True
        finally:
            if error or changelog.status == 'error':
                log.error('Scheduling next update because of error')
                changelog.next_update_at = changelog.calc_next_update_if_error()
                changelog.save()

            log.info('Task done')


@job
def raise_exception():
    1/0
