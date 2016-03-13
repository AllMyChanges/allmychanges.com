# coding: utf-8

import datetime
import copy
import shutil
import arrow
import time

from django.utils import timezone
from allmychanges.utils import (
    discard_seconds,
    update_fields)
from allmychanges.exceptions import (
    UpdateError)
from allmychanges import chat
from allmychanges.version import (
    reorder_versions,
    find_branches,
    version_update_has_wrong_order)
from sortedcontainers import SortedSet
from twiggy_goodies.threading import log


def has_tzinfo(obj):
    return getattr(obj, 'tzinfo', None) is not None


def add_tzinfo(obj):
    return arrow.get(obj).datetime


def update_changelog_from_raw_data3(obj, raw_data):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    from allmychanges.models import Changelog
    from allmychanges.tasks import notify_users_about_new_versions, post_tweet

    start_time = time.time()
    log.info('Updating versions in database')

    now = timezone.now()

    current_versions = SortedSet(
        obj.versions.values_list('number', flat=True))

    discovered_versions = SortedSet(item.version
                                    for item in raw_data)
    all_versions = current_versions | discovered_versions
    new_versions = discovered_versions - current_versions

    if current_versions:
        # now new versions contains only those version numbers which were
        # not discovered yet
        log.debug('Checking if new versions are out of order')
        if hasattr(obj, 'create_issue') and \
           version_update_has_wrong_order(current_versions, new_versions):
            obj.create_issue(type='some-versions-out-of-order',
                             comment='Probably {related_versions} are out of order',
                             related_versions=new_versions)

    if hasattr(obj, 'discovery_history'):
        log.debug('Checking if some "lesser-version-count" issues should be autoresolved')
        # first, we need to check if some old lesser-version-count issues
        # should be closed
        old_issues = obj.issues.filter(type='lesser-version-count',
                                       resolved_at=None)
        for issue in old_issues:
            # we are closing issue if all mentioned versions
            # were discovered during this pass
            if discovered_versions.issuperset(issue.get_related_versions()):
                issue.resolved_at = now
                issue.save(update_fields=('resolved_at',))
                issue.comments.create(message='Autoresolved')
                chat.send(u'Issue of type "{issue.type}" was autoresolved: <https://allmychanges.com/issues/?namespace={issue.changelog.namespace}&name={issue.changelog.name}&resolved|{issue.changelog.namespace}/{issue.changelog.name}>'.format(
                    issue=issue))


        latest_history_item = obj.discovery_history.order_by('id').last()

        if latest_history_item is not None \
           and len(discovered_versions) < latest_history_item.num_discovered_versions:
            previously_discovered_versions = SortedSet(latest_history_item.discovered_versions.split(','))
            missing_versions = previously_discovered_versions - discovered_versions

            obj.create_issue(type='lesser-version-count',
                             comment='This time we didn\'t discover {related_versions} versions',
                             related_versions=missing_versions)

        obj.discovery_history.create(
            discovered_versions=','.join(discovered_versions),
            new_versions=','.join(new_versions),
            num_discovered_versions=len(discovered_versions),
            num_new_versions=len(new_versions))

    if hasattr(obj, 'trackers'):
        trackers = list(obj.trackers.all())
        def add_to_feeds(version):
            for tracker in trackers:
                tracker.add_feed_item(version)
    else:
        add_to_feeds = lambda version: None

    log.debug('Selecting old versions from database')
    all_old_versions = {v.number: v
                        for v in obj.versions.all()}

    log.debug('Updating old versions one by one')

    branches = set(find_branches(all_versions))

    # a list to collect new discovered versions and
    # versions which were unreleased but now have
    # release date
    released_versions = []

    for raw_version in raw_data:
        with log.fields(version_number=raw_version.version):
            log.debug('Updating version')
            version = all_old_versions.get(raw_version.version)

            if version is not None:
                old_version_was_not_released = version.unreleased
            else:
                version = obj.versions.create(number=raw_version.version)
                # old version was not found, this is the same as if
                # it was not released
                old_version_was_not_released = True

            version.unreleased = getattr(raw_version, 'unreleased', False)
            version.filename = getattr(raw_version, 'filename', None)
            version.date = getattr(raw_version, 'date', None)
            version.raw_text = raw_version.content

            version.processed_text = raw_version.processed_content

            if version.discovered_at is None:
                version.discovered_at = getattr(raw_version, 'discovered_at', now)

            version.last_seen_at = now
            version.save()

            this_version_released = not version.unreleased
            if old_version_was_not_released and this_version_released:
                released_versions.append(version)

    month_ago = now - datetime.timedelta(30)
    num_possible_parents = len(branches)

    # if you change this algorithm, then please,
    # update it's description in docs/feed-items.md
    released_versions.reverse()

    notify_about = []

    # we notify only about "tips"
    # or about versions with release date with in month from now()
    # or about some recent versions (if there is no release date)
    for version in released_versions:
        if version.number in branches:
            notify_about.append(version)
        else:
            if version.date:
                if version.date > month_ago:
                    notify_about.append(version)
            else:
                if num_possible_parents > 0:
                    notify_about.append(version)
                    num_possible_parents -= 1

    log.debug('Resorting versions in database')
    reorder_versions(list(obj.versions.all()))

    end_time = time.time()
    with log.fields(update_time=end_time - start_time):
        log.info('Versions in database were updated')

    if notify_about and isinstance(obj, Changelog):
        log.debug('Creating task to notify users')
        notify_users_about_new_versions.delay(
            obj.id,
            [v.id for v in notify_about])

        log.debug('Creating task to post tweet about released version')
        post_tweet.delay(
            changelog_id=obj.id)


from contextlib import contextmanager

@contextmanager
def pdb_enabled():
    import pdb
    previous_value = getattr(pdb, 'enabled', False)
    setattr(pdb, 'enabled', True)

    yield

    setattr(pdb, 'enabled', previous_value)


def update_preview_or_changelog(obj, downloader=None, ignore_problem=False):
    """
    Set ignore_problem=True to not set preview's status to 'error'
    """
    problem = None
    path = None
    found = False
    downloader = downloader or obj.downloader
    downloader_name = downloader if isinstance(downloader, basestring) else downloader['name']

    try:
#        with pdb_enabled():
        obj.set_processing_status(
            'Downloading data using "{0}" downloader'.format(
                downloader_name))
        path = obj.download(downloader)
    except UpdateError as e:
        problem = u', '.join(e.args)
        log.trace().error('Unable to update changelog')
    except Exception as e:
        problem = str(e).decode('utf-8')
        log.trace().error('Unable to update changelog')

    if not path:
        log.trace().error('Unable to update changelog')
        problem = 'Unable to download changelog'
    else:
        try:
            try:
                from allmychanges.parsing.pipeline import processing_pipe
                obj.set_processing_status('Searching versions')
                versions = processing_pipe(path,
                                           obj.get_ignore_list(),
                                           obj.get_search_list(),
                                           obj.xslt)
                if versions:
                    # TODO: тут надо бы сохранять целиком downloader, как dict
                    # чтобы вместе с параметрами
                    update_fields(obj, downloader=downloader_name)
                    obj.set_processing_status('Updating database')
                    update_changelog_from_raw_data3(obj, versions)
                else:
                    print 'raising Update Error'
                    raise UpdateError('Changelog not found')

                found = True
            except UpdateError as e:
                problem = u', '.join(e.args)
                log.trace().error('Unable to update changelog')
            except Exception as e:
                problem = unicode(e)
                log.trace().error(
                    'Unable to update changelog because of unhandled exception')

        finally:
            shutil.rmtree(path)

    if problem is not None:
        if not ignore_problem:
            obj.set_processing_status(problem)
            obj.set_status('error', problem=problem)
    else:
        obj.set_status('success')

    obj.updated_at = timezone.now()
    obj.save()
    return found
