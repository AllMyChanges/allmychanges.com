import re
import datetime
import copy
import shutil
import arrow

from django.utils import timezone
from allmychanges.utils import discard_seconds
from allmychanges.exceptions import (
    UpdateError)
from allmychanges.crawler import search_changelog
from allmychanges.crawler import parse_changelog
from allmychanges import chat
from sortedcontainers import SortedSet
from twiggy_goodies.threading import log


def has_tzinfo(obj):
    return getattr(obj, 'tzinfo', None) is not None


def add_tzinfo(obj):
    return arrow.get(obj).datetime


# TODO: remove
def fill_missing_dates(raw_data):
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
        has_date = item.get('date')

        if not has_date:
            if idx == 0:
                item['discovered_at'] = today
            else:
                if current_date is not None:
                    item['discovered_at'] = current_date
                else:
                    item['discovered_at'] = today - month
        else:
            current_date = item['date']
            item['discovered_at'] = current_date

        item['discovered_at'] = add_tzinfo(item['discovered_at'])
        result.append(item)

    result.reverse()
    return result


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


def get_commit_type(commit_message):
    """Return new or fix or None"""
    commit_message = commit_message.lower()

    if re.search(r'cve-\d+-\d+', commit_message) is not None:
        return 'sec'
    elif 'backward incompatible' in commit_message:
        return 'inc'
    elif 'deprecated' in commit_message:
        return 'dep'
    elif commit_message.startswith('add'):
        return 'new'
    elif commit_message.startswith('new '):
        return 'new'
    elif '[new]' in commit_message:
        return 'new'
    elif commit_message.startswith('fix'):
        return 'fix'
    elif ' fixes' in commit_message:
        return 'fix'
    elif ' fixed' in commit_message:
        return 'fix'
    elif 'bugfix' in commit_message:
        return 'fix'
    elif '[fix]' in commit_message:
        return 'fix'
    return 'new'


# TODO: remove after move to update_changelog_from_raw_data3
def update_changelog_from_raw_data1_3(obj, raw_data, from_vcs=False):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    code_version = 'v2'

    if obj.versions.count() == 0:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates(raw_data)

    for raw_version in raw_data:
        if not raw_version['sections']:
            # we skipe versions without description
            # because some maintainers use these to add
            # unreleased versions into the changelog.
            # Example: https://github.com/kraih/mojo/blob/master/Changes
            continue

        version, created = obj.versions.get_or_create(
            number=raw_version['version'],
            unreleased=raw_version.get('unreleased', False),
            code_version=code_version)

        if from_vcs:
            version.filename = 'VCS'

        version.date = raw_version.get('date')

        if version.discovered_at is None:
            version.discovered_at = raw_version.get('discovered_at', timezone.now())

        version.save()

        version.sections.all().delete()
        for raw_section in raw_version['sections']:
            section = version.sections.create(notes=raw_section.get('notes'),
                                              code_version=code_version)
            for raw_item in raw_section.get('items', []):
                section.items.create(text=raw_item, type=get_commit_type(raw_item))


# TODO: remove after move to update_changelog_from_raw_data3
def update_changelog_from_raw_data(changelog, raw_data, code_version='v1', preview_id=None, from_vcs=False):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""

    if changelog.versions.count() == 0:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates(raw_data)

    for raw_version in raw_data:
        if not raw_version['sections']:
            # we skipe versions without description
            # because some maintainers use these to add
            # unreleased versions into the changelog.
            # Example: https://github.com/kraih/mojo/blob/master/Changes
            continue

        version, created = changelog.versions.get_or_create(
            number=raw_version['version'],
            unreleased=raw_version.get('unreleased', False),
            code_version=code_version,
            preview_id=preview_id)

        if from_vcs:
            version.filename = 'VCS'

        version.date = raw_version.get('date')
#        version.preview_id = preview_id

        if version.discovered_at is None:
            version.discovered_at = raw_version.get('discovered_at', timezone.now())

        version.save()

        version.sections.all().delete()
        for raw_section in raw_version['sections']:
            section = version.sections.create(notes=raw_section.get('notes'),
                                              code_version=code_version)
            for raw_item in raw_section.get('items', []):
                section.items.create(text=raw_item, type=get_commit_type(raw_item))


def update_changelog_from_raw_data3(obj, raw_data):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    code_version = 'v2'

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
                issue.resolved_at = timezone.now()
                issue.save(update_fields=('resolved_at',))
                issue.comments.create(message='Autoresolved')
                chat.send(u'Issue of type "{issue.type}" was autoresolved: <http://allmychanges.com/issues/?namespace={issue.changelog.namespace}&name={issue.changelog.name}&resolved|{issue.changelog.namespace}/{issue.changelog.name}>'.format(
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

    for raw_version in raw_data:
        version, created = obj.versions.get_or_create(
            number=raw_version.version,
            code_version=code_version)

        version.unreleased = getattr(raw_version, 'unreleased', False)
        version.filename = getattr(raw_version, 'filename', None)
        version.date = getattr(raw_version, 'date', None)

        if version.discovered_at is None:
            version.discovered_at = getattr(raw_version, 'discovered_at', timezone.now())

        version.save()

        version.sections.all().delete()
        for raw_section in raw_version.content:
            if isinstance(raw_section, list):
                section = version.sections.create(code_version=code_version)
                for raw_item in raw_section:
                    section.items.create(text=raw_item['text'],
                                         type=raw_item['type'])
            else:
                section = version.sections.create(notes=raw_section,
                                                  code_version=code_version)


# TODO: remove when new update_changelog_from_raw_data3 will be ready
# def update_changelog_from_raw_data2(changelog, raw_data, preview_id=None):
#     """ raw_data should be a list where versions come from
#     more recent to the oldest."""
#     code_version = 'v2'

#     current_versions = SortedSet(
#         changelog.versions.filter(
#             code_version=code_version,
#             preview_id=preview_id).values_list('number',flat=True))

#     discovered_versions = SortedSet(item.version
#                                     for item in raw_data)
#     new_versions = discovered_versions - current_versions

#     if not current_versions:
#         # for initial filling, we should set all missing dates to some values
#         raw_data = fill_missing_dates2(raw_data)
#     else:
#         # now new versions contains only those version numbers which were
#         # not discovered yet
#         if len(new_versions) > 1 and preview_id is None:
#             changelog.create_issue(type='too-many-new-versions',
#                                    comment='I found {0}'.format(
#                                        ', '.join(new_versions)))

#     latest_history_item = changelog.discovery_history.order_by('-id').last()

#     if latest_history_item is not None \
#        and len(discovered_versions) < latest_history_item.num_discovered_versions:
#         previously_discovered_versions = SortedSet(latest_history_item.discovered_versions.split(','))
#         missing_versions = previously_discovered_versions - discovered_versions

#         if preview_id is None:
#             changelog.create_issue(type='lesser-version-count',
#                                    comment='This time we didn\'t discover {0} versions'.format(
#                                        u', '.join(missing_versions)))

#     changelog.discovery_history.create(
#         discovered_versions=','.join(discovered_versions),
#         new_versions=','.join(new_versions),
#         num_discovered_versions=len(discovered_versions),
#         num_new_versions=len(new_versions))

#     for raw_version in raw_data:
#         version, created = changelog.versions.get_or_create(
#             number=raw_version.version,
#             code_version=code_version,
#             preview_id=preview_id)

#         version.unreleased = getattr(raw_version, 'unreleased', False)
#         version.filename = getattr(raw_version, 'filename', None)
#         version.date = getattr(raw_version, 'date', None)

#         if version.discovered_at is None:
#             version.discovered_at = getattr(raw_version, 'discovered_at', timezone.now())

#         version.save()

#         version.sections.all().delete()
#         for raw_section in raw_version.content:
#             if isinstance(raw_section, list):
#                 section = version.sections.create(code_version=code_version)
#                 for raw_item in raw_section:
#                     section.items.create(text=raw_item['text'],
#                                          type=raw_item['type'])
#             else:
#                 section = version.sections.create(notes=raw_section,
#                                                   code_version=code_version)


def parse_changelog_file(filename):
    """This function should always return a list.
    """
    with open(filename) as f:
        text = f.read()
        try:
            decoded = text.decode('utf-8')
        except UnicodeDecodeError:
            return []
        else:
            return parse_changelog(decoded)


def search_changelog2(path):
    """Searches a file which contains large
    amount of changelog-like records"""

    filenames = search_changelog(path)

    raw_data = [(parse_changelog_file(filename), filename)
                for filename in filenames]
    if raw_data:
        raw_data.sort(key=lambda item: len(item[0]),
                      reverse=True)

        filename, raw_data = raw_data[0][1], raw_data[0][0]
        # only return data if we found some records
        if len(raw_data) > 1 or 'changelog' in filename.lower():
            return filename, raw_data

    return None, None


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
        problem = unicode(e)
        log.trace().error('Unable to update changelog')

    if path:
        try:
            try:
                from allmychanges.parsing.pipeline import processing_pipe, vcs_processing_pipe
                obj.set_processing_status('searching-versions')
                versions = processing_pipe(path,
                                           obj.get_ignore_list(),
                                           obj.get_search_list())
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


# def update_changelog(changelog, preview_id=None):
#     # TODO: remove when update_preview_or_changelog will be ready
#     changelog.filename = None

#     if preview_id is None:
#         ignore_list = changelog.get_ignore_list()
#         search_list = changelog.get_search_list()
#         download = changelog.download
#     else:
#         preview = changelog.previews.get(pk=preview_id)
#         ignore_list = preview.get_ignore_list()
#         search_list = preview.get_search_list()
#         download = preview.download


#     try:
#         path = download()
#     except UpdateError:
#         raise
#     except Exception:
#         logging.getLogger('update-changelog').exception('unhandled')
#         raise UpdateError('Unable to download sources')

#     try:
#         try:
#             from allmychanges.parsing.pipeline import processing_pipe
#             versions = processing_pipe(path, ignore_list, search_list)
#             #print 'Num versions from pipeline:', len(versions)
#             if not versions:
#                 logging.getLogger('update-changelog2').debug('updating v2 from vcs')
#                 versions = vcs_processing_pipe(path, ignore_list, search_list)
#                 #print 'Num versions from VCS:', len(raw_data)

#             if not versions:
#                 raise UpdateError('Changelog not found')
#             update_changelog_from_raw_data2(changelog, versions, preview_id=preview_id)

#         except UpdateError:
#             raise
#         except Exception:
#             logging.getLogger('update-changelog').exception('unhandled')
#             raise UpdateError('Unable to parse or extract sources')

#         # try:
#         #     filename, raw_data = search_changelog2(path)

#         #     if raw_data:
#         #         changelog.filename = os.path.relpath(filename, path)
#         #         changelog.save()
#         #     else:
#         #         raw_data = extract_changelog_from_vcs(path)

#         # except UpdateError:
#         #     raise
#         # except Exception:
#         #     logging.getLogger('update-changelog').exception('unhandled')
#         #     raise UpdateError('Unable to parse or extract sources')

#         # if not raw_data:
#         #     raise UpdateError('Changelog not found')

#         # try:
#         #     update_changelog_from_raw_data(changelog, raw_data, preview_id=preview_id)
#         # except Exception:
#         #     logging.getLogger('update-changelog').exception('unhandled')
#         #     raise UpdateError('Unable to update database')

#     finally:
#         shutil.rmtree(path)

#         # we only need to change updated_at if this
#         # wasn't preview update
#         if preview_id is None:
#             changelog.updated_at = timezone.now()
#             changelog.save()
