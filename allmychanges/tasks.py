# -*- coding: utf-8 -*-
import logging
import datetime

from django.db.models import Count
from django.utils import timezone
from django.conf import settings
from allmychanges.utils import (
    count_time,
    update_changelog,
    UpdateError)

from twiggy_goodies.django_rq import job
from twiggy_goodies.threading import log


@job
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
def schedule_updates(reschedule=False, packages=[]):
    from .models import Changelog

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
def delete_empty_changelogs():
    from .models import Changelog
    Changelog.objects.annotate(Count('packages'), Count('versions')) \
                     .filter(packages__count=0, versions__count=0) \
                     .delete()


@job
def update_changelog_task(source):
    with log.fields(source=source):
        from .models import Changelog
        changelog = Changelog.objects.get(source=source)

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
            changelog.next_update_at = timezone.now() + datetime.timedelta(1)
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
