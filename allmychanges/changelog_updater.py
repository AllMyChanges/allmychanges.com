import re
import datetime
import copy
import logging
import shutil
import os.path

from django.utils import timezone
from allmychanges.utils import discard_seconds
from allmychanges.downloader import (
    get_downloader)
from allmychanges.exceptions import (
    UpdateError)
from allmychanges.vcs_extractor import extract_changelog_from_vcs
from allmychanges.crawler import search_changelog
from allmychanges.crawler import parse_changelog


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
    today = discard_seconds(datetime.datetime.utcnow())
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
    today = discard_seconds(datetime.datetime.utcnow())
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


def update_changelog_from_raw_data2(changelog, raw_data, preview_id=None):
    """ raw_data should be a list where versions come from
    more recent to the oldest."""
    code_version = 'v2'

    if changelog.versions.filter(code_version=code_version).count() == 0:
        # for initial filling, we should set all missing dates to some values
        raw_data = fill_missing_dates2(raw_data)

    for raw_version in raw_data:
        version, created = changelog.versions.get_or_create(
            number=raw_version.version,
            code_version=code_version,
            preview_id=preview_id)

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


def update_changelog(changelog, preview_id=None):
    changelog.filename = None

    if preview_id is None:
        ignore_list = changelog.get_ignore_list()
        check_list = changelog.get_check_list()
        download = changelog.download
    else:
        preview = changelog.previews.get(pk=preview_id)
        ignore_list = preview.get_ignore_list()
        check_list = preview.get_check_list()
        download = preview.download


    try:
        path = download()
    except UpdateError:
        raise
    except Exception:
        logging.getLogger('update-changelog').exception('unhandled')
        raise UpdateError('Unable to download sources')

    try:
        try:
            from allmychanges.parsing.pipeline import processing_pipe
            versions = processing_pipe(path,
                                       ignore_list,
                                       check_list)
            if versions:
                update_changelog_from_raw_data2(changelog, versions, preview_id=preview_id)
            else:
                logging.getLogger('update-changelog2').debug('updating v2 from vcs')
                raw_data = extract_changelog_from_vcs(path)
                update_changelog_from_raw_data(changelog, raw_data, code_version='v2', preview_id=preview_id, from_vcs=True)

        except Exception:
            logging.getLogger('update-changelog2').exception('unhandled')

        try:
            filename, raw_data = search_changelog2(path)

            if raw_data:
                changelog.filename = os.path.relpath(filename, path)
                changelog.save()
            else:
                raw_data = extract_changelog_from_vcs(path)

        except UpdateError:
            raise
        except Exception:
            logging.getLogger('update-changelog').exception('unhandled')
            raise UpdateError('Unable to parse or extract sources')

        if not raw_data:
            raise UpdateError('Changelog not found')

        try:
            update_changelog_from_raw_data(changelog, raw_data, preview_id=preview_id)
        except Exception:
            logging.getLogger('update-changelog').exception('unhandled')
            raise UpdateError('Unable to update database')

    finally:
        shutil.rmtree(path)

        # we only need to change updated_at if this
        # wasn't preview update
        if preview_id is None:
            changelog.updated_at = timezone.now()
            changelog.save()