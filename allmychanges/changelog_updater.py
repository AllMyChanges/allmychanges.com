import datetime
import copy
import shutil
import arrow

from django.utils import timezone
from allmychanges.utils import discard_seconds
from allmychanges.exceptions import (
    UpdateError)
from allmychanges import chat
from allmychanges.version import reorder_versions
from sortedcontainers import SortedSet
from twiggy_goodies.threading import log


def has_tzinfo(obj):
    return getattr(obj, 'tzinfo', None) is not None


def add_tzinfo(obj):
    return arrow.get(obj).datetime


def fill_missing_dates2(raw_data):
    """Algorithm.

    If first item has no date, then it is today.
    If Nth item has date, then assume it is a current_date.
    If Nth item has no date and we have current_date, then assume item's
    date is current_date.
    If Nth item has no date and we have no current_date, then assume, it
    is a now() - month and act like we have it.
    """
    result = []
    today = discard_seconds(timezone.now())
    month = datetime.timedelta(30)
    current_date = None

    for idx, item in enumerate(reversed(raw_data)):
        item = copy.deepcopy(item)
        has_date = getattr(item, 'date', None)

        if not has_date:
            if idx == 0:
                item.discovered_at = today
            else:
                if current_date is not None:
                    item.discovered_at = current_date
                else:
                    item.discovered_at = today - month
        else:
            current_date = item.date
            item.discovered_at = current_date

        item.discovered_at = add_tzinfo(item.discovered_at)
        result.append(item)

    result.reverse()
    return result


def update_changelog_from_raw_data3(obj, raw_data):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    from allmychanges.models import Changelog
    from allmychanges.tasks import notify_users_about_new_versions, post_tweet

    code_version = 'v2'
    now = timezone.now()

    current_versions = SortedSet(
        obj.versions.filter(
            code_version=code_version).values_list('number',flat=True))

    discovered_versions = SortedSet(item.version
                                    for item in raw_data)
    new_versions = discovered_versions - current_versions

    if not current_versions:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates2(raw_data)
    else:
        # now new versions contains only those version numbers which were
        # not discovered yet
        if len(new_versions) > 1 and hasattr(obj, 'create_issue'):
            obj.create_issue(type='too-many-new-versions',
                             comment='I found {related_versions}',
                             related_versions=new_versions)

    if hasattr(obj, 'discovery_history'):
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

    new_versions_ids = []
    for raw_version in raw_data:
        with log.fields(version_number=raw_version.version,
                        code_version=code_version):
            version, created = obj.versions.get_or_create(
                number=raw_version.version,
                code_version=code_version)
            if created:
                new_versions_ids.append(version.id)

        version.unreleased = getattr(raw_version, 'unreleased', False)
        version.filename = getattr(raw_version, 'filename', None)
        version.date = getattr(raw_version, 'date', None)
        version.raw_text = raw_version.content
        version.processed_text = raw_version.processed_content

        if version.discovered_at is None:
            version.discovered_at = getattr(raw_version, 'discovered_at', now)

        version.last_seen_at = now

        version.save()

    reorder_versions(list(obj.versions.all()))

    if new_versions_ids and isinstance(obj, Changelog):
        notify_users_about_new_versions.delay(
            obj.id, new_versions_ids)
        post_tweet.delay(
            changelog_id=obj.id)


def update_preview_or_changelog(obj):
    problem = None
    path = None

    try:
        obj.set_processing_status('downloading')
        path = obj.download()
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
                from allmychanges.parsing.pipeline import processing_pipe, vcs_processing_pipe
                obj.set_processing_status('searching-versions')
                versions = processing_pipe(path,
                                           obj.get_ignore_list(),
                                           obj.get_search_list(),
                                           obj.xslt)
                #print 'Num versions from pipeline:', len(versions)

                if not versions:
                    log.debug('updating v2 from vcs')
                    obj.set_processing_status('processing-vcs-history')
                    versions = vcs_processing_pipe(path,
                                                   obj.get_ignore_list(),
                                                   obj.get_search_list())

                    #print 'Num versions from VCS:', len(raw_data)

                if versions:
                    obj.set_processing_status('updating-database')
                    update_changelog_from_raw_data3(obj, versions)
                else:
                    raise UpdateError('Changelog not found')

            except UpdateError as e:
                problem = u', '.join(e.args)
                log.trace().error('Unable to update changelog')
            except Exception as e:
                problem = unicode(e)
                log.trace().error('Unable to update changelog')

        finally:
            shutil.rmtree(path)

    if problem is not None:
        obj.set_status('error', problem=problem)
    else:
        obj.set_status('success')

    obj.set_processing_status('')
    obj.updated_at = timezone.now()
    obj.save()
