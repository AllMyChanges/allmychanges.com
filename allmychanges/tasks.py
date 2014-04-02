# -*- coding: utf-8 -*-
import logging
import datetime

from django_rq import job
from allmychanges.utils import count_time
from django.utils import timezone


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
    try:
        package.update()
        package.next_update_at = timezone.now() + datetime.timedelta(1)
    except Exception:
        package.next_update_at = timezone.now() + datetime.timedelta(0, 1 * 60 * 60)
        raise
    finally:
        package.save()
