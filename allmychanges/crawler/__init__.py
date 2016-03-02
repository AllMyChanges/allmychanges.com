# coding: utf-8
import os
import re
from dateutil.parser import parse as date_parser
from html2text import html2text


#RE_DATE = re.compile(r'(.*\s|\s?|.*\()(?P<date>\d{1,4}[.-]+\d{1,4}[.-]+\d{1,4})')
_months = ('January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December')

def abbr_month(name):
    if len(name) > 3:
        return name[:3] + '.'
    return name

_months = _months \
          + tuple(name[:3] for name in _months) \
          + tuple(abbr_month(name) for name in _months)

# вот эти штуки (?:[^.0-9]|$) в начале и конце,
# нужны, чтобы мы не пытались искать даты в составе номеров версий
RE_DATE_STR = r"""
              # date shouldn't start with dot or alfanumeric or 'v' or 'r' character
              (?:[^.0-9vr]|^)(?P<date>(
              # 2009-05-23, 2009.05.23, 2009/05/23 but not 2009.05-23
              \num_year(?P<delimiter1>[./-])\d{1,2}(?P=delimiter1)\d{1,2} |

              # 05/23/2009
              \d{1,2}(?P<delimiter3>[./-])\d{1,2}(?P=delimiter3)\num_year |

              # 05-23-2009 or 05.23.2009 but not 05.23-2009
              \d{1,2}(?P<delimiter2>[.-])\d{1,2}(?P=delimiter2)\num_year |

              # 24 Apr 2014
              # 6th December 2013
              \d{1,2}(rd|st|rd|th|nd)?\ \month\ \num_year |


              # May 23rd 2014
              # April 28, 2014
              # Apr 01, 2013
              # Aug. 17, 2012
              \month[ ]+\d{1,2}(rd|st|rd|th)?,?\ \num_year |

              # Fri Aug  8 19:12:51 PDT 2014
              [A-Z][a-z]{2}\ [A-Z][a-z]{2}\ +\d{1,2}\ \d{2}:\d{2}:\d{2}\ [A-Z]{3}\ \num_year
              ))(?!\.[0-9])""".replace(
                  r'\month',
                  r'({0})'.format('|'.join(_months))) \
                  .replace(
                      r'\num_year',
                      r'(?:(?:19|20)\d{2})')

RE_DATE = re.compile(RE_DATE_STR, re.VERBOSE)


IGNORE_DIRS = ['.git', '.hg', '.svn']


def list_files(path='.'):
    """Recursivly walks through files and returns them as iterable.

    All filenames are relative to given path (this is important!)
    """
    for root, dirs, files in os.walk(path):
        for dir_to_ignore in IGNORE_DIRS:
            if dir_to_ignore in dirs:
                dirs.remove(dir_to_ignore)

        for f in files:
            yield os.path.relpath(
                os.path.join(root, f),
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


_version_regexes = [
    # in the beginning
    r'^{ver}.*',
    # in the middle of line but not far from beginning
    # version number should be preceeded by a star or whitespace
    # i belive, star is used to make version number bold
    # or emphasized in markdown
    r'^[^ ].{{,20}}?[* ]{ver}',
    # or this could be a similar case, when version number
    # is a part of a filename like this
    # release-notes/0.1.1.md
    # or txt/release-1.2.2p1
    # or dist/kafka/0.8.0/RELEASE_NOTES.html
    # but not in this case
    # <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
    r'[/a-zA-Z-](?<!HTTP/){ver}(?:\.[^\d]|/?)(?![^ ]*")',
]

_version_regexes = [item.format(ver=(r'\(?' # version number could be surrounded by brackets
                                     r'(?:r|v|v\.)?(?P<ver>(?:'  # version can have a prefix like v0.1.2 or v.0.1.2
                                                                 # or r0.1.2
                                       r'(?:' # complex version
                                         r'(?:\d+(?:\.\d+)+(-[a-z0-9.]+[a-z0-9])?)'     # main part
                                         r'(-?(([a-zA-Z0-9.-]+[a-zA-Z0-9])|[a-zA-Z]))?' # rc1, beta2 or maybe -something123 like suffix or .BETA-123
                                                                                        # or just 1.0.2a
                                         r'(_\d+)?'                # or _12343 suffix like in the damn https://github.com/Test-More/TB2/blob/master/Changes
                                       r')' # end of complex version
                                       r'|' # or
                                       r'(?:' # simple version
                                         r'(?<=[ _-](?:v|r))\d+' # versions with on number should be
                                                       # prefixed with ' v' or ' r'
                                                       # or something like '_v' or '-v'
                                         r'|'
                                         r'(?<=^(?:v|r))\d+' # versions with on number should be
                                                       # prefixed with '^v' or '^r'
                                       r')'   # end of simple version
                                     r'))'))
                    for item in _version_regexes]


RE_BUMP_LINE_STR = ur"""^
           [Bb]ump\ to.*                |
           [Bb]ump\ .*version           |
           [Bb]ump\ .*release           |
           [Bb]uild\ for\ v?\d+\.\d+.*  |
           [Uu]pdate\ to\ v?\d+\.\d+.*  |
           [Vv]\d+\.\d+.*               |
           \d+\.\d+.*
$"""

RE_BUMP_LINE = re.compile(RE_BUMP_LINE_STR, re.VERBOSE)


COMMON_SUFFIXES_STR = ur"""
  -notes    |
  .txt      |
  .html     |
  .rst      |
  .md       |
  .markdown |
$"""
RE_COMMON_SUFFIXES = re.compile(COMMON_SUFFIXES_STR, re.VERBOSE)


def remove_common_suffixes(version):
    """
    We need this function because were unable to write
    single complex regex which will extract version numbers
    from strings like "releases/v1.2.3-rc1.a1.txt"
    """
    new_version = RE_COMMON_SUFFIXES.sub(u'', version)
    if new_version == version:
        return new_version
    else:
        return remove_common_suffixes(new_version)


def _extract_version(line):
    if line:
        for date_str in RE_DATE.finditer(line):
            line = line.replace(date_str.group('date'), u'')

        # now remove frequent words
        line = re.sub(ur'version|release notes|for',
                      u'', line, flags=re.IGNORECASE)
        # remove duplicate spaces
        line = re.sub(ur'\s{2,}', u' ', line)

        line = line.strip()
        for i in _version_regexes:
            match = re.search(i, line)
            if match is not None:
                version = match.group('ver')
                version = remove_common_suffixes(version)

                tokens = line.replace(version, '').split()
                tokens = [token for token in tokens
                          if re.match(ur'[-:_]+', token) is None]

                # we ignore long lines because probably
                # they are not headers we are looking for
                if len(tokens) > 6:
                    return None

                # we ignore lines where too many numbers
                has_numbers = lambda token: re.search(ur'\d', token) is not None
                tokens_with_numbers = len(filter(None, map(has_numbers, tokens)))
                if tokens_with_numbers > 3:
                    return None

                # also, we ignore versions ending with .x
                # or with suffix -notes which sometimes used
                # in filenames: https://github.com/numpy/numpy/tree/master/doc/release
                lowered_line = line.lower()
                if version.endswith('.x') \
                   or version.endswith('-notes') \
                   or 'since' in lowered_line \
                   or 'upgrading to ' in lowered_line:
                    return None

                return version


def _extract_date(line):
    """Return date that is in line"""
    for date_str in RE_DATE.finditer(line):
        try:
            parsed = date_parser(date_str.group('date'),
                                 dayfirst=True)
            return parsed.date()
        except Exception:
            continue


def _parse_item(line):
    """For lines like:

    - Blah minor
    or
    * Blah minor
    or even
    *) Damn you, Nginx!

    returns tuple (True, 3, 'Blah minor')

    For item like:

        Blah minor

    returns  tuple (False, 4, 'Blah minor')

    For items like:

        Feature #1155: Log packet payloads in eve alerts

    returns tuple (True, 0, 'Feature #1155: Log packet payloads in eve alerts')

    for others - (False, 0, None)
    """
    # for items
    match = re.search(r'^[ ]*[*-]\)?[ ]+', line)
    if match is not None:
        ident = len(match.group(0))
        return (True, ident, line[ident:])

    match = re.search(r'^\S+(\s\S+){1,2}: .*', line)
    if match is not None:
        return (True, 0, line)

    # for idented lines
    match = re.search(r'^[ \t]+', line)
    if match is not None:
        ident = len(match.group(0))
        return (False, ident, line[ident:])
    return (False, 0, None)


# def _starts_with_ident(line, ident):
#     """Returns true, if line starts with given number of spaces."""
#     if ident <= 0:
#         return False
#     match = re.search(r'^[ ]{%s}[^ ]' % ident, line)
#     return match is not None


# def parse_changelog(text):
#     changelog = []
#     current_version = None
#     # here we'll track each line distance from corresponding
#     # line with version number
#     line_in_current_version = None
#     current_section = None
#     current_item = None
#     current_ident = None

#     if '<html' in text and \
#        '<body' in text:
#         text = html2text(text)

#     lines = text.split('\n')

#     for line in lines:
#         # skip lines like
#         # ===================
#         if line and line == line[0] * len(line):
#             continue

#         if line_in_current_version is not None:
#             line_in_current_version += 1

#         is_item, ident, text = _parse_item(line)
#         if is_item and current_section:
#             # wow, a new changelog item was found!
#             current_item = [text]
#             current_ident = ident
#             current_section['items'].append(current_item)
#         else:
#             version = _extract_version(line)
#             v_date = _extract_date(line.replace(version, '') if version else line)
#             if version is not None:
#                 # we found a possible version number, lets
#                 # start collecting the changes!
#                 current_version = dict(version=version, sections=[])
#                 line_in_current_version = 1
#                 current_section = None
#                 current_item = None
#                 current_ident = None

#                 changelog.append(current_version)

#             elif _starts_with_ident(line, current_ident) and current_item:
#                 # previous changelog item has continuation on the
#                 # next line
#                 current_item.append(line[current_ident:])
#             else:
#                 # if this is not item, then this is a note
#                 if current_version is not None:

#                     if not current_section or current_section['items']:
#                         # if there is items in the current section
#                         # and we found another plaintext part,
#                         # then start another section
#                         current_section = dict(notes=[line], items=[])
#                         current_version['sections'].append(current_section)
#                     else:
#                         # otherwise, continue note of the curent
#                         # section
#                         current_section['notes'].append(line)

#             if current_version:
#                 if line_in_current_version < 3 and 'unreleased' in line.lower():
#                     current_version['unreleased'] = True

#                 if v_date and current_version.get('date') is None:
#                     current_version['date'] = v_date

#     # usually versions go from most recent to
#     # older, but we should return them in chronological
#     # order
#     changelog.reverse()
#     return _finalize_changelog(changelog)


# def _finalize_changelog(changelog):
#     """A helper to squash notes and items."""
#     dct_versions = dict()
#     result = list()

#     # either add a space at the end, nor replace with
#     # \n if empty
#     process_note_line = lambda text: text + ' ' if text else '\n'

#     for version in changelog:
#         # squash texts
#         for section in version['sections']:
#             section['items'] = [
#                 ' '.join(item).strip()
#                 for item in section['items']]
#             section['notes'] = ''.join(
#                 process_note_line(note)
#                 for note in section['notes']).strip()

#         # remove empty sections
#         version['sections'] = [section for section in version['sections']
#                                if section['notes'] or section['items']]

#         version_data = dct_versions.get(version['version'])
#         if version_data:
#             # add current params to already existed
#             version_data['sections'].extend(version['sections'])
#         else:
#             dct_versions[version['version']] = version
#             result.append(version)

#     return result
