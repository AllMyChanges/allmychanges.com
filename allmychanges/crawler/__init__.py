import os
import re
from dateutil.parser import parse as date_parser
from html2text import html2text


#RE_DATE = re.compile(r'(.*\s|\s?|.*\()(?P<date>\d{1,4}[.-]+\d{1,4}[.-]+\d{1,4})')
RE_DATE = re.compile(r'(?P<date>\d{1,4}[.-]+\d{1,4}[.-]+\d{1,4})')


IGNORE_DIRS = ['.git', '.hg', '.svn']

def list_files(path='.'):
    """Recursivly walks through files and returns them as iterable.

    All filenames are relative to given path (this is important!)
    """
    for root, dirs, files in os.walk(path):
        for dir_to_ignore in IGNORE_DIRS:
            if dir_to_ignore in dirs:
                dirs.remove(dir_to_ignore)
                
        for file in files:
            yield os.path.relpath(
                os.path.join(root, file),
                path)


include_predicates = [
    lambda x: 'change' in x,
    lambda x: 'news' in x,
    lambda x: 'release' in x,
    lambda x: 'history' in x,
    lambda x: 'readme' in x,
]


exclude_predicates = [
    lambda x: x.endswith('.sh'),
    lambda x: x.endswith('.py'),
    lambda x: x.count('/') > 4,
]


def _filter_changelog_files(filenames):
    for filename in filenames:
        if any(p(filename.lower()) for p in include_predicates) and \
                not any(p(filename.lower()) for p in exclude_predicates):
            yield filename


def search_changelog(path='.'):
    """Searches changelog-like files in the current directory."""
    filenames = list(list_files(path=path))
    filenames = [os.path.join(path, filename)
                 for filename in _filter_changelog_files(filenames)]
    return filenames



def _extract_version(line):
    extract_regexps = [
        r'^(\d+\.\d+\.\d+|\d+\.\d+).*',
        r'^[^ ].*?(\d+\.\d+\.\d+|\d+\.\d+)',
    ]
    for i in extract_regexps:
        match = re.search(i, line)
        if match is not None:
            return match.group(1)


def _extract_date(line):
    """Return date that is in line"""
    for date_str in RE_DATE.finditer(line):
        try:
            return date_parser(date_str.group('date')).date()
        except:
            continue


def _parse_item(line):
    """For lines like:

     - Blah minor

    returns tuple (True, 3, 'Blah minor')
    for others - (False, 0, None)
    """
    match = re.search(r'^[ ]*[*-][ ]+', line)
    if match is not None:
        ident = len(match.group(0))
        return (True, ident, line[ident:])
    return (False, 0, None)


def _starts_with_ident(line, ident):
    """Returns true, if line starts with given number of spaces."""
    if ident <= 0:
        return False
    match = re.search(r'^[ ]{%s}[^ ]' % ident, line)
    return match is not None


def parse_changelog(text):
    changelog = []
    current_version = None
    current_section = None
    current_item = None
    current_ident = None

    if '<html' in text and \
       '<body' in text:
        text = html2text(text)

    lines = text.split('\n')

    for line in lines:
        # skip lines like
        # ===================
        if line and line == line[0] * len(line):
            continue

        is_item, ident, text = _parse_item(line)
        if is_item and current_section:
            # wow, a new changelog item was found!
            current_item = [text]
            current_ident = ident
            current_section['items'].append(current_item)
        else:
            version = _extract_version(line)
            v_date = _extract_date(line.replace(version, '') if version else line)
            if version is not None:
                # we found a possible version number, lets
                # start collecting the changes!
                current_version = dict(version=version, sections=[])
                current_section = None
                current_item = None
                current_ident = None

                changelog.append(current_version)

            elif _starts_with_ident(line, current_ident) and current_item:
                # previous changelog item has continuation on the
                # next line
                current_item.append(line[current_ident:])
            else:
                # if this is not item, then this is a note
                if current_version is not None:
                    if not current_section or current_section['items']:
                        # if there is items in the current section
                        # and we found another plaintext part,
                        # then start another section
                        current_section = dict(notes=[line], items=[])
                        current_version['sections'].append(current_section)
                    else:
                        # otherwise, continue note of the curent
                        # section
                        current_section['notes'].append(line)

            if v_date and current_version and current_version.get('date') is None:
                current_version['date'] = v_date

    return _finalize_changelog(changelog)


def _finalize_changelog(changelog):
    """A helper to squash notes and items."""
    dct_versions = dict()
    result = list()

    # either add a space at the end, nor replace with
    # \n if empty
    process_note_line = lambda text: text + ' ' if text else '\n'
            
    for version in changelog:
        # squash texts
        for section in version['sections']:
            section['items'] = [
                ' '.join(item).strip()
                for item in section['items']]
            section['notes'] = ''.join(
                process_note_line(note)
                for note in section['notes']).strip()

        # remove empty sections
        version['sections'] = [section for section in version['sections']
                               if section['notes'] or section['items']]

        version_data = dct_versions.get(version['version'])
        if version_data:
            # add current params to already existed
            version_data['sections'].extend(version['sections'])
        else:
            dct_versions[version['version']] = version
            result.append(version)

    return result
