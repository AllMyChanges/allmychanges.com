# -*- coding: utf-8 -*-
import logging
import datetime
import time

from django.db.models import Count
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from allmychanges.utils import (
    count_time,
    update_changelog,
    UpdateError)

from twiggy_goodies.django_rq import job
from twiggy_goodies.threading import log


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


@job
@transaction.commit_on_success
def schedule_updates(reschedule=False, packages=[]):
    from .models import Changelog

    stale_changelogs = Changelog.objects.filter(
        processing_started_at__lt=timezone.now() - datetime.timedelta(0, 60 * 60))

    num_stale = len(stale_changelogs)
    
    if num_stale > 0:
        log.info('{0} stale changelogs were found', num_stale)
        stale_changelogs.update(processing_started_at=None)

    if packages:
        changelogs = Changelog.objects.filter(packages__name__in=packages).distinct()
    else:
        changelogs = Changelog.objects.annotate(Count('packages')).filter(packages__count__gt=0)

    log.info('Rescheduling {0} changelogs update'.format(len(changelogs)))

    if not reschedule:
        changelogs = changelogs.filter(next_update_at__lte=timezone.now())

    for changelog in changelogs:
        update_changelog_task.delay(changelog.source)

    delete_empty_changelogs.delay()


@job
@transaction.commit_on_success
def delete_empty_changelogs():
    from .models import Changelog
    Changelog.objects.annotate(Count('packages'), Count('versions')) \
                     .filter(packages__count=0, versions__count=0) \
                     .delete()


@job
@transaction.commit_on_success
def update_changelog_task(source):
    with log.fields(source=source):
        log.error('Starting task')
        from .models import Changelog

        changelog = None
        tries = 10
        while changelog is None and tries > 0:
            try:
                changelog = Changelog.objects.get(source=source)
            except Changelog.DoesNotExist:
                log.error('Changelog with source={source} not found'.format(
                    **locals()))
                time.sleep(10)
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

        next_update_if_error = timezone.now() + datetime.timedelta(0, 1 * 60 * 60)

        try:
            changelog.problem = None
            changelog.processing_started_at = timezone.now()
            changelog.save()

            update_changelog(changelog)
            # TODO: create more complext algorithm to calculate this time
            changelog.next_update_at = timezone.now() + datetime.timedelta(0, 60 * 60)
        except UpdateError, e:
            changelog.problem = ', '.join(e.args)
        except Exception, e:
            if settings.DEBUG:
                changelog.problem = unicode(e)
            else:
                changelog.problem = 'Unknown error'

            log.info('Unable to update changelog with source {0}'.format(source))
            changelog.next_update_at = next_update_if_error
            raise
        finally:
            changelog.processing_started_at = None
            changelog.save()


@job
def raise_exception():
    1/0
