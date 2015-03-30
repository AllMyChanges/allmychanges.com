# -*- coding: utf-8 -*-
import datetime

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from allmychanges.downloader import normalize_url
from allmychanges.utils import count, first_sentences
from allmychanges.notifications import slack
from allmychanges.changelog_updater import update_preview_or_changelog
from allmychanges import chat

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


def wait_chat_threads(func):
    """We need to wait all chat threads to exit
    to ensure that all messages were sent before
    task done.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            chat.wait_threads()

    return wrapper


@singletone()
@job
@transaction.atomic
@wait_chat_threads
def schedule_updates(reschedule=False, packages=[]):
    from .models import Changelog

    if packages:
        changelogs = Changelog.objects.filter(name__in=packages).distinct()
    else:
        changelogs = Changelog.objects.only_active()

    if not reschedule:
        changelogs = changelogs.filter(next_update_at__lte=timezone.now())

    num_changelogs = len(changelogs)
    count('task.schedule_updates.scheduling.count', num_changelogs)
    log.info('Rescheduling {0} changelogs update'.format(num_changelogs))

    for changelog in changelogs:
        changelog.schedule_update()


@singletone('preview')
@job('preview', timeout=600)
@transaction.atomic
@wait_chat_threads
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
@wait_chat_threads
def update_changelog_task(source):
    with log.fields(source=source):
        log.info('Starting task')
        processing_started_at = timezone.now()
        error = True
        error_description = None

        try:
            from .models import Changelog
            changelog = Changelog.objects.get(source=source)
            update_preview_or_changelog(changelog)

            changelog.last_update_took = (timezone.now() - processing_started_at).seconds
            changelog.next_update_at = changelog.calc_next_update()
            changelog.save()
            error = False
        except Exception as e:
            error_description = unicode(e)
            log.trace().error('Error during changelog update')
        finally:
            if error or changelog.status == 'error':
                changelog.paused_at = timezone.now()
                changelog.create_issue('auto-paused',
                                       comment=u'Paused because of error: "{0}"'.format(
                                           error_description or changelog.problem or 'unknown'))
                changelog.save()

            log.info('Task done')


@job
def raise_exception():
    1/0


@singletone()
@job('default', timeout=600)
@transaction.atomic
@wait_chat_threads
def notify_users_about_new_versions(changelog_id, version_ids):
    """Notifies a changelog's trackers with their preferred methods
    """
    from .models import Changelog, Version

    with log.fields(changelog_id=changelog_id):
        log.info('Starting task')
        changelog = Changelog.objects.get(pk=changelog_id)
        trackers = changelog.trackers.all()

        versions = Version.objects.filter(pk__in=version_ids)
        slack_versions = u', '.join(
            '<http://allmychanges.com{0}|{1}>'.format(
                version.get_absolute_url(),
                version.number)
            for version in versions)

        slack_text = u'Look, new {versions_form} of <{url}|{namespace}/{name}> {was_form} found: {versions}'.format(
            url='http://allmychanges.com' + changelog.get_absolute_url(),
            namespace=changelog.namespace,
            name=changelog.name,
            versions=slack_versions,
            versions_form='version' + (len(version_ids) > 1 and u's' or u''),
            was_form=(len(version_ids) > 1) and 'were' or 'was')

        for user in trackers:
            if user.slack_url:
                slack.send(url=user.slack_url, text=slack_text)



def process_appstore_url(url):
    from .models import AutocompleteData, DESCRIPTION_LENGTH
    source = url.source
    # we need this because autocomplete compares
    # these urls agains Changelog model where sources
    # are normalized
    # print '\nprocessing-appstore:', source
    with log.name_and_fields('process_appstore_url', source=source):
        try:
            log.info('Processing')
            if url.autocomplete_data is None:
                source, username, repo, data = \
                    normalize_url(source, return_itunes_data=True)

                try:
                    description = first_sentences(
                        data['description'],
                        DESCRIPTION_LENGTH)
                except RuntimeError:
                    with log.fields(description=data['description'][:DESCRIPTION_LENGTH * 2]):
                        log.trace().error('Unable to get first sentences')
                        description = data['description'][:DESCRIPTION_LENGTH].replace('\n', ' ')

                url.autocomplete_data = \
                        AutocompleteData.objects.create(
                    origin='app-store',
                    title=u'{0} by {1}'.format(
                        data['trackName'],
                        data['sellerName']),
                    description=description,
                    source=source,
                    icon=data['artworkUrl60'])
                url.save()
        except:
            log.trace().error('Unable to process')


@singletone()
@job('default', timeout=60 * 60)
@transaction.atomic
@wait_chat_threads
def process_appstore_batch(batch_id, size=100):
    """Notifies a changelog's trackers with their preferred methods
    """
    from .models import AppStoreBatch

    print 'Processing batch', batch_id
    with log.name_and_fields('process_appstore_batch', batch_id=batch_id):
        log.info('Starting task')
        batch = AppStoreBatch.objects.get(pk=batch_id)
        urls = list(batch.urls.filter(autocomplete_data=None))
        for url in urls:
            process_appstore_url(url)

        start_new_appstore_batch.delay(size)
    print 'Done with batch', batch_id


from django.db import transaction

@job('default', timeout=60)
@transaction.atomic
def start_new_appstore_batch(size=100, batch_id=None):
    """Creates a new batch of AppStore urls to be processed.
    """
    from .models import AppStoreBatch, AppStoreUrl
    if batch_id is None:
        batch = AppStoreBatch.objects.create()
    else:
        batch = AppStoreBatch.objects.get(pk=batch_id)

    ids = list(AppStoreUrl.objects.filter(batch=None).values_list('id', flat=True)[:size])
    print '{0} ids were selected for batch {1}'.format(len(ids), batch.id)
    AppStoreUrl.objects.filter(pk__in=ids, batch=None).update(batch=batch)

    urls_count = AppStoreUrl.objects.filter(batch=batch).count()
    if urls_count == 0:
        free_urls_count = AppStoreUrl.objects.filter(batch=None).count()
        if free_urls_count > 0:
            print 'BAD, we aquired 0 urls but there is {0} free urls in database, retrying'.format(
                free_urls_count)
            start_new_appstore_batch.delay(size, batch_id=batch.id)
    else:
        print 'Batch {0} queued'.format(batch.id)
        process_appstore_batch.delay(batch.id, size=size)


def restart_old_appstore_batches():
    from .models import AppStoreBatch
    hour_ago = timezone.now() - datetime.timedelta(0, 60 * 60)
    ids = AppStoreBatch.objects.filter(urls__autocomplete_data=None,
                                       created__lte=hour_ago)
    ids = ids.values_list('id', flat=True).distinct()

    for pk in ids:
        process_appstore_batch.delay(pk)
