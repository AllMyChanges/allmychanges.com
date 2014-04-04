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
def schedule_updates(reschedule=False):
    from .models import Package

    packages = Package.objects.all()

    if not reschedule:
        packages = packages.filter(next_update_at__lte=timezone.now())

    for package in packages:
        update_package.delay(package.id)


@job
def update_package(package_id):
    from .models import Package
    package = Package.objects.get(pk=package_id)
    
    changelog = package.changelog
    if changelog.processing_started_at is not None:
        return # because somebody already processing this changelog
    
    next_update_if_error = timezone.now() + datetime.timedelta(0, 1 * 60 * 60)
    
    try:
        changelog.problem = None
        changelog.processing_started_at = timezone.now()
        changelog.save()
        
        update_changelog(package)
        package.next_update_at = timezone.now() + datetime.timedelta(1)
    except UpdateError, e:
        changelog.problem = ', '.join(e.args)
    except Exception, e:
        if settings.DEBUG:
            changelog.problem = unicode(e)
        else:
            changelog.problem = 'Unknown error'
            
        print 'Unable to update changelog for package {0}'.format(package)
        package.next_update_at = next_update_if_error
        raise
    finally:
        changelog.processing_started_at = None
        package.save()
        changelog.save()
