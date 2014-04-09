# -*- coding: utf-8 -*-
import logging
import datetime

from django_rq import job
from django.utils import timezone
from django.conf import settings
from allmychanges.utils import (
    count_time,
    update_changelog,
    UpdateError)


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

    if packages :
        changelogs = Changelog.objects.filter(package__name__in=packages).distinct()
    else:
        changelogs = Changelog.objects.all()

    if not reschedule:
        changelogs = changelogs.filter(next_update_at__lte=timezone.now())

    for changelog in changelogs:
        update_changelog_task.delay(changelog.source)


@job
def update_changelog_task(source):
    from .models import Changelog
    changelog = Changelog.objects.get(source=source)
    
    if changelog.processing_started_at is not None:
        return # because somebody already processing this changelog
    
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
            
        print 'Unable to update changelog with source {0}'.format(source)
        changelog.next_update_at = next_update_if_error
        raise
    finally:
        changelog.processing_started_at = None
        changelog.save()
