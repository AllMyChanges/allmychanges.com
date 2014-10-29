# coding: utf-8
import re
import codecs
import copy
import itertools
import os
import tempfile
import shutil
import envoy

from operator import itemgetter
from collections import defaultdict

from allmychanges.crawler import _extract_version, _extract_date
from allmychanges.utils import get_change_type
from allmychanges.env import Environment
from django.conf import settings


CHANGELOG_LIKE_FILENAMES = ('change', 'release', 'news', 'history')
EXTENSIONS_TO_CHECK = {'.rst', '.md', '.markdown', '.txt', '.htm', '.html'}


def filename_looks_like_a_changelog(filename):
    filename = filename.lower()
    return any((item in filename)
               for item in CHANGELOG_LIKE_FILENAMES)


def compare_versions(left, right):
    return left.date < right.date \
        and left.version < right.version


def parse_changelog(raw_changelog):
    # TODO: похоже этот код нигде не используется
    chunks = raw_changelog.get_chunks()
    versions = itertools.chain(*[chunk.get_versions()
                                 for chunk in chunks])
    versions = sorted(versions, compare_versions)
    return versions


##############################
## NEW
##############################


def strip_outer_tag(text):
    # TODO: move to utils
    match = re.match('^<(.*?)>', text)
    if match is not None:
        tag = match.group(1)
        closing = '</{}>'.format(tag)
        if text.endswith(closing):
            result = text[len(tag) + 2: - len(closing)]
            return result

    return text


def get_files(env, walk=os.walk):
    """
    Uses: env.ignore_list, env.check_list and env.dirname.
    """

    ignore_list = env.ignore_list
    check_list = env.check_list

    def in_ignore_list(filename):
        for ignore_prefix in ignore_list:
            if filename.startswith(ignore_prefix):
                return True
        return False

    def search_in_check_list(filename):
        for prefix, markup in check_list:
            if filename.startswith(prefix):
                return True, markup
        return False, None

    for root, dirs, files in walk(env.dirname):
        for filename in files:
            full_filename = os.path.join(root, filename)
            rel_filename = os.path.relpath(full_filename, env.dirname)

            low_filename = rel_filename.lower()
            _, ext = os.path.splitext(low_filename)

            if ext not in EXTENSIONS_TO_CHECK \
               and not filename_looks_like_a_changelog(low_filename):
                continue

            if not in_ignore_list(rel_filename):
                attrs = dict(type='filename',
                             filename=full_filename)

                if check_list:
                    found, markup = search_in_check_list(rel_filename)
                    if found:
                        if markup:
                            attrs['markup'] = markup
                        yield env.push(**attrs)
                else:
                    yield env.push(**attrs)


# TODO: remove
def read_files(root, filenames):
    for filename in filenames:
        with codecs.open(filename, 'r', 'utf-8') as f:
            try:
                content = create_file(
                    os.path.relpath(filename, root),
                    f.read())
            except Exception:
                continue

            yield content


def read_file(obj):
    with codecs.open(obj.filename, 'r', 'utf-8') as f:
        try:
            yield obj.push(
                type='file_content',
                filename=os.path.relpath(obj.filename, obj.dirname),
                content=f.read())
        except Exception:
            pass


# TODO: remove
def parse_files(file_objects):
    """Outputs separate sections (header + notes/items)
    from every file.
    """
    for obj in file_objects:
        markup = get_markup(obj)
        if markup is not None:
            versions = globals().get('parse_{0}_file'.format(markup))(obj)
            for version in versions:
                # this information will be required late
                version['filename'] = get_file_name(obj)
                yield version

def parse_file(env):
    """Outputs separate sections (header + notes/items)
    from every file.
    """
    markup = getattr(env, 'markup', None)
    if not markup:
        markup = get_markup(env.filename, env.content)

    if markup is not None:
        versions = globals().get('parse_{0}_file'.format(markup))(env)
        for version in versions:
            yield version



def parse_markdown_file(obj):
    import markdown2
    html = markdown2.markdown(obj.content)
    return parse_html_file(obj.push(content=html))


def parse_plain_file(obj):
    from allmychanges.crawler import _parse_item, _starts_with_ident
    current_title = None
    # here we'll track each line distance from corresponding
    # line with version number
    current_sections = []
    current_section = None
    current_ident = None

    for line in obj.content.split('\n'):
        # skip lines like
        # ===================
        if line and line == line[0] * len(line):
            continue

        is_item, ident, text = _parse_item(line)
        version = _extract_version(line)

        # we have to check if item is not version
        # because of python-redis changelog format
        # where versions is unordered list with sublists
        if is_item and not version:
            if not isinstance(current_section, list):
                # wow, a new changelog item list was found
                if current_section is not None:
                    current_sections.append(current_section)
                current_section = []

            current_ident = ident
            current_section.append(text)
        else:
            if version is not None:
                # we found a possible version number, lets
                # start collecting the changes!
                if current_section:
                    current_sections.append(current_section)

                if current_title and current_sections:
                    yield obj.push(type='file_section',
                                   title=current_title,
                                   content=current_sections)

                current_title = line
                current_section = None
                current_sections = []
                current_ident = None

            elif _starts_with_ident(line, current_ident) and isinstance(current_section, list):
                # previous changelog item has continuation on the
                # next line
                current_section[-1] += '\n' + line[current_ident:]
            else:
                # if this is not item, then this is a note
                if current_title:
                    if isinstance(current_section, list):
                        # if there is items in the current section
                        # and we found another plaintext part,
                        # then start another section
                        current_sections.append(current_section)
                        current_section = None

                    if current_section is None:
                        if line:
                            current_section = line
                    else:
                        current_section += u'\n' + line

    if current_section:
        current_sections.append(current_section)

    if current_title and current_sections:
        # if current_section:
        #     current_sections.append(current_section)
        yield obj.push(type='file_section',
                       title=current_title,
                       content=current_sections)



def search_conf_py(root_dir, doc_filename):
    parts = doc_filename.split('/')
    while parts:
        parts = parts[:-1]
        filename = os.path.join(
            root_dir, '/'.join(parts), 'conf.py')
        if os.path.exists(filename):
            return filename


def parse_rst_file(obj):
    path = obj.cache.get('rst_builder_temp_path')
    if path is None:
        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
        obj.cache['rst_builder_temp_path'] = path

    conf_py = obj.cache.get('rst_conf_py')
    if conf_py is None:
        conf_py = search_conf_py(obj.dirname, obj.filename)
        if conf_py:
            obj.cache['rst_conf_py'] = conf_py

            # if there is a config for sphinx
            # then use it!
            shutil.copy(conf_py, os.path.join(path, 'conf.py'))

            # also, use all directories starting from underscore
            # for django it is _ext and _themes, for other
            # projects it maky work or not
            # if it does not work for some important projects, then
            # we'll need a more wise algorithm which will try
            # to figure out conf.py dependencies

            conf_py_dir = os.path.dirname(conf_py)
            for name in os.listdir(conf_py_dir):
                fullname = os.path.join(conf_py_dir, name)
                if name.startswith('_') and os.path.isdir(fullname):
                    destination = os.path.join(path, name)
                    shutil.copytree(fullname, destination)
        else:
            obj.cache['rst_conf_py'] = 'was created'

        with codecs.open(os.path.join(path, 'conf.py'), 'a', 'utf-8') as f:
            f.write("master_doc = 'index'\n")
            f.write("source_suffix = '.rst'\n")

    with codecs.open(os.path.join(path, 'index.rst'), 'w', 'utf-8') as f:
        f.write(obj.content)

    envoy.run('rm -fr {0}/output/index.html'.format(path))
    envoy.run('sphinx-build -b html {0} {0}/output'.format(path))

    with codecs.open(os.path.join(path, 'output', 'index.html'), 'r', 'utf-8') as f:
        html = f.read()

    return parse_html_file(obj.push(content=html))


# TODO: remove
def create_section(title, content=[], version=None, date=None):
    """Each section has a title and a list of content objects.
    Each content object is either a text or a list object.
    """
    result = dict(title=title, content=content)
    if version:
        result['version'] = version
    result['date'] = date
    return result


get_section_title = itemgetter('title')
get_section_content = itemgetter('content')


def parse_html_file(obj):
    import lxml.html
    parsed = lxml.html.document_fromstring(obj.content)
    headers = [tag for tag in parsed.iter()
               if tag.tag in ('h1', 'h2', 'h3', 'h4')]


    def create_list(el):
        def inner_html(el):
            text = lxml.html.tostring(el).strip()
            text = strip_outer_tag(text)
            return text

        return map(inner_html, el.getchildren())

    def create_notes(children):
        """ This function returns content of the current
        version. It is a list where each item either a HTML
        fragment or a list of html fragments.
        If it is a list of html fragments, then each item
        SHOULD NOT be wrapped into a node like <li> or <p>.
        """
        current_text = ''
        for el in children:
            if el.tag == 'ul':
                if current_text:
                    yield current_text.strip()
                    current_text = ''
                yield create_list(el)
            else:
                current_text += lxml.html.tostring(el)

        if current_text:
            yield current_text.strip()

    headers = [(header.tag, header.text, header.itersiblings())
               for header in headers]

    # use whole document and filename as a section
    headers.insert(0, ('h0',
                       obj.filename,
                       parsed.find('body').iterchildren()))

    def is_header_tag(ch):
        if isinstance(ch.tag, basestring):
            return not ch.tag.startswith('h') or ch.tag > tag

    for tag, text, all_children in headers:
        children = itertools.takewhile(
            is_header_tag,
            all_children)
        sections = list(create_notes(children))
        yield obj.push(type='file_section',
                       title=text,
                       content=sections)


def create_file(name, content):
    return dict(name=name, content=content)

get_file_name = itemgetter('name')
get_file_content = itemgetter('content')


def get_markup(filename, content):
    filename = filename.lower()

    if filename.endswith('.rst') \
       or':func:`' in content:
        return 'rst'

    if filename.endswith('.md') \
       or re.search('^[=-]{3,}', content, re.MULTILINE) is not None \
       or re.search('^#{2,}', content, re.MULTILINE) is not None \
       or re.search('\[.*?\]\(.*\)', content, re.MULTILINE) is not None \
       or re.search('\[.*?\]\[.*\]', content, re.MULTILINE) is not None:
        return 'markdown'

    return 'plain'


def filter_versions(sections):
    """Searches parts of the files which looks like
    changelog pieces.
    """
    for section in sections:
        version = _extract_version(get_section_title(section))
        if version:
            new_section = copy.deepcopy(section)
            new_section['version'] = version
            yield new_section


def filter_version(section):
    """Searches parts of the files which looks like
    changelog pieces.
    """
    version = _extract_version(section.title)
    if version:
        yield section.push(type='almost_version',
                           version=version)


def extract_metadata(version):
    """Tries to extract date and list items' type.
    """
    def _all_dates(iterable):
        for item in iterable:
            date = _extract_date(item)
            if date:
                yield date

    def _all_list_items():
        for content_part in version.content:
            if isinstance(content_part, list):
                for item in content_part:
                    yield item
            elif isinstance(content_part, basestring):
                yield content_part

    def mention_unreleased(text):
        # here we limit our scoupe of searching
        # unreleased keywords
        # because if keyword is somewhere far from
        # the beginning, than probably it is unrelated
        # to the version itself
        text = text[:300]

        keywords = ('unreleased', 'under development',
                    'not yet released',
                    'release date to be decided')
        lowered = text.lower()
        for keyword in keywords:
            if keyword in lowered:
                return True
        return False

    all_dates = _all_dates(itertools.chain([version.title],
                                           _all_list_items()))

    new_version = version.push(type='prerender_items')
    try:
        new_version.date = all_dates.next()
    except StopIteration:
        pass

    if mention_unreleased(version.title):
        new_version.unreleased = True

    def process_content(idx, content_part):
        if isinstance(content_part, basestring):
            # here we limit our scoupe of searching
            # unreleased keywords
            # because if keyword is somewhere far from
            # the beginning, than probably it is unrelated
            # to the version itself
            if idx < 3 and mention_unreleased(content_part):
                new_version.unreleased = True

            return content_part
        else:
            # here we process list items
            return [{'type': get_change_type(item),
                     'text': item}
                    for item in content_part]
    new_version.content = [process_content(idx, content)
                           for idx, content
                           in enumerate(version.content)]
    yield new_version


def prerender_items(version):
    new_version = version.push(type='version')
    from ..templatetags.allmychanges_tags import process_cve
    from django.template.defaultfilters import capfirst
    from bleach import clean

    def remove_html_markup(text):
        # import pdb; pdb.set_trace()  # DEBUG
        # bleach.ALLOWED_TAGS
        # [u'a', u'abbr', u'acronym', u'b', u'blockquote', u'code', u'em', u'i', u'li', u'ol', u'strong', u'ul']
        # bleach.ALLOWED_ATTRIBUTES
        # {u'a': [u'href', u'title'], u'acronym': [u'title'], u'abbr': [u'title']}
        # bleach.ALLOWED_STYLES
        # []
        #
        return clean(text,
                     tags=[u'a', u'abbr', u'acronym', u'b', u'blockquote',
                           u'code', u'em', u'i', u'li', u'ol', u'strong', u'ul', # these are default
                           u'p', # we allow paragraphs cause they are fine
                           u'h1', u'h2', u'h3', u'h4', # headers are ok too
                           u'tt', # monospace
                           u'div', # dont see why it should be prohibited
                           u'span', # and spans too
                           u'pre',
                       ],
                     attributes={u'a': [u'href', u'title'],
                                 u'acronym': [u'title'],
                                 u'abbr': [u'title']},
                     styles=[])

    def apply_filters(text):

        for flt in [remove_html_markup, process_cve, capfirst]:
            text = flt(text)
        return text

    def process_content(content):
        if isinstance(content, basestring):
            return apply_filters(content)
        else:
            return [dict(item,
                         text=apply_filters(item['text']))
                    for item in content]

    new_version.content = map(process_content, version.content)
    yield new_version

def group_by_path(versions):
    """ Returns a dictionary, where keys are a strings
    with directories, starting from '.' and values
    are lists with all versions found inside this directory.
    """
    result = defaultdict(list)
    for version in versions:
        path = version.filename.split(u'/')
        path = [name + u'/'
                for name in path[:-1]] + path[-1:]

        while path:
            result[''.join(path)].append(version)
            path = path[:-1]
    return result


def filter_trash_versions(versions):
    grouped = group_by_path(versions)

    def calc_score(source):
        score = 10

        # add points if name has explicit point that there is
        # some version information
        if filename_looks_like_a_changelog(source):
            score += 1000

        # and add point for each version inside this source
        score += len(grouped[source])
        return score

    sources = [(calc_score(source), source)
               for source in grouped]
    sources.sort(reverse=True)

    best_source = sources[0][1]

    return grouped[best_source]


def processing_pipe(root, ignore_list=[], check_list=[]):
    root_env = Environment()
    root_env.type = 'directory'
    root_env.dirname = root
    root_env.ignore_list = ignore_list
    root_env.check_list = check_list
    # a dictionary to keep data between different processor's invocations
    root_env.cache = {}

    processors = dict(directory=get_files,
                      filename=read_file,
                      file_content=parse_file,
                      file_section=filter_version,
                      almost_version=extract_metadata,
                      prerender_items=prerender_items)

    def run_pipeline(obj, get_processor=lambda obj: None):
        processor = get_processor(obj)
        if processor is None:
            yield obj
        else:
            for new_obj in processor(obj):
                for obj in run_pipeline(new_obj,
                                        get_processor=get_processor):
                    yield obj

    versions = list(
        run_pipeline(root_env,
                     get_processor=lambda obj: processors.get(obj.type)))

    if not versions:
        return []

    def compare_version_numbers(left, right):
        try:
            # it is fair to compare version numbers
            # as tuples of integers
            left = tuple(map(int, left.split('.')))
            right = tuple(map(int, right.split('.')))
        except Exception:
            # but some versions can't be represented with integers only
            # in this case we'll fall back to lexicographical comparison
            pass

        return cmp(left, right)

    def compare_versions(left, right):
        result = compare_version_numbers(left.version, right.version)
        if result != 0:
            return result

        left_keys_count = len(left.keys())
        right_keys_count = len(right.keys())

        if left_keys_count < right_keys_count:
            return -1
        if left_keys_count > right_keys_count:
            return 1

        return 0

    # TODO: вот это надо будет использовать для сбора статистику по исходникам
    # from itertools import groupby
    # grouped = groupby(versions, lambda x: x.filename)
    # grouped1 = [(key, list(value)) for key, value in grouped]
    # grouped2 = [(key, len(value)) for key, value in grouped1]

    # print '\n'.join(map('{0[0]}: {0[1]}'.format, sorted(grouped2)))

    # now we'll select a source with maximum number of versions
    # but not the root directory
    versions = filter_trash_versions(versions)

    # using customized comparison we make versions which
    # have less metadata go first
    versions.sort(cmp=compare_versions)
    # and grouping them by version number
    # we leave only unique versions with maximum number of metadata

    versions = dict((version.version, version)
                    for version in versions)

    # and finally we'll prepare a list, sorted by version number
    versions = versions.values()
    versions.sort(cmp=lambda left, right: \
                  compare_version_numbers(left.version, right.version))

    for key, value in root_env.cache.items():
        if key.endswith('_temp_path'):
            shutil.rmtree(value)

    return versions



# file|parse -> sections|filter_versions -> create_raw_versions|sort
