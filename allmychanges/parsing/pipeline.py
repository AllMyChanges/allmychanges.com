# coding: utf-8
import re
import codecs
import copy
import os
import tempfile
import shutil
import envoy
import lxml.html

from operator import itemgetter
from collections import defaultdict
from functools import wraps
from itertools import islice, chain, takewhile
from pkg_resources import parse_version
from rq.timeouts import JobTimeoutException

from allmychanges.crawler import _extract_version, _extract_date
from allmychanges.utils import get_change_type, strip_long_text, first
from allmychanges.env import Environment
from django.conf import settings
from twiggy_goodies.threading import log


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
    versions = chain(*[chunk.get_versions()
                       for chunk in chunks])
    versions = sorted(versions, compare_versions)
    return versions


##############################
## NEW
##############################

def node_tostring(node, with_tail=False):
    """Convert's html node to string if it is not a string yet.
    """
    if isinstance(node, basestring):
        return node
    return lxml.html.tostring(node, with_tail=with_tail)



# TODO: move to utils
def strip_outer_tag(text):
    get_children = lxml.html.etree.XPath("text()|*")

    def rec(items):
        if len(items) == 1:
            item = items[0]
            if isinstance(item, basestring):
                return item

            if isinstance(item, lxml.html.HtmlComment):
                return item.tail or ''
            else:
                children = get_children(items[0])

            return rec(children)
        else:
            return u''.join(
                map(node_tostring,
                    items))

    items = lxml.html.fragments_fromstring(text)
    return rec(items)


def get_files(env, walk=os.walk):
    """
    Uses: env.ignore_list, env.search_list and env.dirname.
    """

    ignore_list = env.ignore_list
    search_list = env.search_list

    def in_ignore_list(filename):
        for ignore_prefix in ignore_list:
            if filename.startswith(ignore_prefix):
                return True
        return False

    def search_in_search_list(filename):
        for prefix, markup in search_list:
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

                if search_list:
                    found, markup = search_in_search_list(rel_filename)
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
            content = f.read()
            yield obj.push(
                type='file_content',
                filename=os.path.relpath(obj.filename, obj.dirname),
                content=content)
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
        parser = globals().get('parse_{0}_file'.format(markup))
        versions = parser(env)
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

    def format_section(section):
        if isinstance(section, list):
            return messages_to_html(section)
        return u'<p>{0}</p>'.format(section)

    def format_content(sections):
        return u'\n'.join(map(format_section, sections))


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
                                   content=format_content(current_sections))

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
        yield obj.push(type='file_section',
                       title=current_title,
                       content=format_content(current_sections))



def search_conf_py(root_dir, doc_filename):
    parts = doc_filename.split('/')
    while parts:
        parts = parts[:-1]
        filename = os.path.join(
            root_dir, '/'.join(parts), 'conf.py')
        if os.path.exists(filename):
            return filename


def parse_rst_file(obj):
    cfg_override = """
html_theme = 'epub'
html_theme_options = {
    'relbar1': 'false',
    'footer': 'false',
}
master_doc = 'index'
source_suffix = '.rst'
"""

    with log.fields(filename=obj.filename):
        dirname = os.path.dirname(obj.filename)

        path_key = 'rst_builder_temp_path:' + dirname
        path = obj.cache.get(path_key)
        if path is None:
            path = tempfile.mkdtemp(dir=obj.cache['tmp-dir'])
            obj.cache[path_key] = path

        def create_conf_py():
            filename = os.path.join(path, 'conf.py')
            if os.path.exists(filename):
                os.unlink(filename)
            with codecs.open(filename, 'a', 'utf-8') as f:
                f.write(cfg_override)

        def copy_conf_py():
            filename = os.path.join(path, 'conf.py')

            # if there is a config for sphinx
            # then use it!
            log.info('Copying conf.py')
            shutil.copy(conf_py, filename)

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
                    if not os.path.exists(destination):
                        shutil.copytree(fullname, destination)

            with codecs.open(os.path.join(path, 'conf.py'), 'a', 'utf-8') as f:
                f.write(cfg_override)


        def generate_html():
            """Tries to generate HTML from reST with current config.
            If operation was successful, returns content of HTML file.
            """
            with codecs.open(os.path.join(path, 'index.rst'), 'w', 'utf-8') as f:
                f.write(obj.content)

            envoy.run('rm -fr {0}/output/index.html'.format(path))
            envoy.run('sphinx-build -b html {0} {0}/output'.format(path))

            output_filename = os.path.join(path, 'output', 'index.html')
            if os.path.exists(output_filename):
                with codecs.open(output_filename, 'r', 'utf-8') as f:
                    return f.read()


        conf_py_key = 'rst_conf_py:' + dirname
        conf_py = obj.cache.get(conf_py_key)

        if conf_py is None:
            conf_py = search_conf_py(obj.dirname, obj.filename)
            if not conf_py:
                conf_py = 'fake-conf.py'
                log.info('Will use fake conf.py')

        html = None
        if conf_py != 'fake-conf.py':
            copy_conf_py()
            html = generate_html()
        if html is None:
            create_conf_py()
            if conf_py != 'fake-conf.py':
                log.info('Attempt to use package\'s conf.py has failed')
            conf_py = 'fake-conf.py'
            html = generate_html()

        if html is None:
            log.info('Unable to parse this rst file')
            html = ''

        obj.cache[conf_py_key] = conf_py
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
    """
    Uses fields `content` and `filename` to generate new file_sections.
    """
    if not obj.content:
        # Some files are empty, document_fromstring raises exception on them
        return

    try:
        parser = lxml.html.HTMLParser(encoding='utf-8')
        parsed = lxml.html.document_fromstring(obj.content.encode('utf-8'),
                                               parser=parser)
    except Exception as e:
        # these errors are ignored
        if str(e) == 'Document is empty':
            return
        raise

    headers = [tag for tag in parsed.iter()
               if tag.tag in ('h1', 'h2', 'h3', 'h4')]


    def create_full_content(children):
        """Just serialize all childrens and join result."""
        strings = map(lxml.html.tostring, children)
        return u''.join(strings)


    headers = [(header.tag, header.text_content(), header.itersiblings())
               for header in headers]

    def is_header_tag(ch):
        if isinstance(ch.tag, basestring):
            return not ch.tag.startswith('h') or ch.tag > tag

    def process_header(parent, tag, text, all_children):
        children = list(takewhile(
            is_header_tag,
            all_children))

        full_content = create_full_content(children)
        return parent.push(type='file_section',
                           title=text.strip(),
                           content=full_content)

    # use whole document and filename as a section
    body = parsed.find('body')
    if body is not None:
        root = process_header(obj, 'h0', obj.filename, body.iterchildren())
        yield root

        # and then process all other items
        for tag, text, all_children in headers:
            yield process_header(root, tag, text, all_children)


def create_file(name, content):
    return dict(name=name, content=content)

get_file_name = itemgetter('name')
get_file_content = itemgetter('content')


def get_markup(filename, content):
    filename = filename.lower()
    content_head = content[:1000].lower().strip()

    if filename.endswith('.rst'):
        return 'rst'

    if filename.endswith('.md'):
        return 'markdown'

    if filename.endswith('.html') or filename.endswith('.htm'):
        return 'html'

    if ':func:`' in content \
       or re.search('`[^` ]+`_', content, re.MULTILINE) is not None \
       or re.search('``[^` ]+``', content, re.MULTILINE) is not None:
        return 'rst'

    if re.search('^[=-]{3,}', content, re.MULTILINE) is not None \
       or re.search('^#{2,}', content, re.MULTILINE) is not None \
       or re.search('\[.*?\]\(.*\)', content, re.MULTILINE) is not None \
       or re.search('\[.*?\]\[.*\]', content, re.MULTILINE) is not None:
        return 'markdown'

    if content_head.startswith('<!doctype ') \
       or content_head.startswith('<html'):
        return 'html'

    return 'plain'


# def filter_versions(sections):
#     """Searches parts of the files which looks like
#     changelog pieces.
#     """
#     for section in sections:
#         version = _extract_version(get_section_title(section))

#         if version:
#             new_section = copy.deepcopy(section)
#             new_section['version'] = version
#             yield new_section


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
    def mention_unreleased(text):
        # here we limit our scoupe of searching
        # unreleased keywords
        # because if keyword is somewhere far from
        # the beginning, than probably it is unrelated
        # to the version itself
        keywords = ('unreleased', 'under development',
                    'not yet released',
                    'release date to be decided')
        lowered = text.lower()
        for keyword in keywords:
            if keyword in lowered:
                return True
        return False

    first_lines = version.content.split(u'\n', 3)[:3]
    first_lines.insert(0, version.title)

    new_version = version.push(type='prerender_items')
    for line in first_lines:
        date = _extract_date(line[:200])
        if date:
            new_version.date = date
            break
        if mention_unreleased(line[:200]):
            new_version.unreleased = True
            break
    yield new_version


def highlight_keywords(text):
    check = lambda pattern, label: (ur'(?P<before>^|\s|>)(?P<word>{0}?)(?P<after>$|\s|\.|,|:|!|<)'.format(pattern),
                                    ur'\g<before>BEG-highlight-{0}-BEG\g<word>END-highlight-END\g<after>'.format(label))

    checks = [
        check(ur'fix(ed|es|ing)? a bug', u'fix'),
        check(ur'bug fix(ed|es|ing)?', u'fix'),
        check(ur'fix(ed|es|ing)?', u'fix'),
        check(ur'bug(fix(es)?)?', u'fix'),

        check(ur'deprecated', u'dep'),

        check(ur'security', u'sec'),
        check(ur'xss', u'sec'),

        check(ur'backward incompatible', u'inc'),
        check(ur'removed', u'inc'),
    ]
    checks = [(re.compile(pattern, re.IGNORECASE), replacement)
              for pattern, replacement in checks]

    for pattern, replacement in checks:
        text = pattern.sub(replacement, text)

    text = re.sub(ur'BEG-highlight-(?P<label>.*?)-BEG(?P<text>.*?)END-highlight-END',
                  ur'<span class="changelog-highlight-\g<label>">\g<text></span>',
                  text)
    return text


def prerender_items(version):
    new_version = version.push(type='version')
    from ..templatetags.allmychanges_tags import process_cve
    from django.template.defaultfilters import capfirst
    from bleach import clean

    def remove_html_markup(text, *args, **kwargs):
        # removing reST's fucking field-list from our nice changelog item
        text = re.sub(ur'<table class="docutils field-list".*?</table>', u'', text, flags=re.DOTALL | re.M)

        text = clean(text,
                     tags=[u'table', 'colgroup', 'col', 'tr', 'td', 'th', 'tbody', 'thead',
                           u'a', u'abbr', u'acronym', u'b', u'blockquote',
                           u'code', u'em', u'i', u'li', u'ol', u'strong', u'ul', # these are default
                           u'p', # we allow paragraphs cause they are fine
                           u'h1', u'h2', u'h3', u'h4', # headers are ok too
                           u'del', u'strike', u's',
                           u'tt', # monospace
                           u'div', # dont see why it should be prohibited
                           u'span', # and spans too
                           u'pre', u'cite',
                           u'br', # allow linebreaks because they are generated by VCS extractor.
                       ],
                     attributes={u'a': [u'href', u'title'],
                                 u'acronym': [u'title'],
                                 u'abbr': [u'title']},
                     styles=[])
        return text

    def apply_filters(text):
        """Accepts whole item and returns another item with processed text.
        Item could be a dictionary or plain text."""
        for flt in [remove_html_markup,
                    process_cve,
                    capfirst,
                    highlight_keywords]:
            text = flt(text)

        return text

    # def prerender_content(html):
    #     # TODO insert markup using get_change_type(item)
    #     return html

    new_version.processed_content = apply_filters(version.content)
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


def processing_pipe(*args, **kwargs):
    processors = dict(directory=get_files,
                      filename=read_file,
                      file_content=parse_file,
                      file_section=filter_version,
                      almost_version=extract_metadata,
                      prerender_items=prerender_items)
    return _processing_pipe(processors, *args, **kwargs)


from allmychanges.vcs_extractor import (
    get_versions_from_vcs,
    messages_to_html
)

def vcs_processing_pipe(*args, **kwargs):
    processors = dict(directory=get_versions_from_vcs,
                      almost_version=extract_metadata,
                      prerender_items=prerender_items)
    versions = _processing_pipe(processors, *args, **kwargs)

    # don't show single unreleased version because it means we found nothing
    if len(versions) == 1 and versions[0].unreleased:
        versions = []

    return versions


def _processing_pipe(processors, root, ignore_list=[], search_list=[]):
    def print_(item):
        t = item.type
        def get_content(content):
            if isinstance(content, basestring):
                return strip_long_text(content, 20)
            if isinstance(content, dict):
                return dict(content, text=get_content(content['text']))
            return map(get_content, content)

        print ''

        if t == 'filename':
            print item.__repr__(('filename',))
        elif t == 'file_content':
            print item.__repr__(('filename',
                             #    ('content', get_content)
                             ))
        elif t == 'file_section':
            print item.__repr__(('title',
                             #    ('content', get_content)
                             ))
        elif t in ('almost_version', 'prerender_items', 'version'):
            print item.__repr__(('filename',
              #                   ('content', get_content),
                                 'version', 'title'))
        else:
            print item

    def print_tree(env):
        while env._parent:
            env = env._parent

        def print_env(env, padding):
            t = env.type
            comment = u''
            if t == 'version':
                comment = env.version
            elif t == 'filename':
                comment = env.filename
            elif t == 'file_section':
                comment = env.title

            print u'{padding}{t} {comment}'.format(
                padding=u' ' * padding * 2,
                t=t,
                comment=comment)
            for child in env._children:
                child = child()
                if child is not None:
                    print_env(child, padding + 1)
        print_env(env, 0)


    def catch_errors(processor):
        @wraps(processor)
        def wrapper(*args, **kwargs):

            try:
                for item in processor(*args, **kwargs):
#                    if processor.__name__ in ('get_files', 'prerender_items'):
#                    print_(item)
                    yield item
            except JobTimeoutException:
                raise
            except Exception:
                with log.name_and_fields('processing-pipe', processor=processor.__name__):
                    log.trace().error('Unable to process items')

        return wrapper

    processors = dict((name, catch_errors(processor))
                      for name, processor in processors.items())

    # pipeline's core engine which executes all steps for each item
    # passing it from one processor to another
    def run_pipeline(obj, get_processor=lambda obj: None):
        processor = get_processor(obj)
        if processor is None:
            yield obj
        else:
            for new_obj in processor(obj):
                for obj in run_pipeline(new_obj,
                                        get_processor=get_processor):
                    yield obj

    root_env = Environment()
    root_env.type = 'directory'
    root_env.dirname = root
    root_env.ignore_list = ignore_list
    root_env.search_list = search_list
    # a dictionary to keep data between different processor's invocations
    root_env.cache = {'tmp-dir': tempfile.mkdtemp(dir=settings.TEMP_DIR)}

    try:
        versions = list(
            run_pipeline(root_env,
                         get_processor=lambda obj: processors.get(obj.type)))
    finally:
        shutil.rmtree(root_env.cache['tmp-dir'])

    if not versions:
        return []

    def compare_version_numbers(left, right):
        try:
            # it is fair to compare version numbers
            # as tuples of integers
            left = parse_version(left)
            right = parse_version(right)
        except Exception:
            # but some versions can't be represented with integers only
            # in this case we'll fall back to lexicographical comparison
            pass

        return cmp(left, right)

    def compare_version_metadata(left, right):
        result = compare_version_numbers(left.version, right.version)
        if result != 0:
            return result

        left_keys_count = len(left.keys())
        right_keys_count = len(right.keys())

        if left_keys_count < right_keys_count:
            return -1
        if left_keys_count > right_keys_count:
            return 1

        left_content_length = len(left.content)
        right_content_length = len(right.content)

        if left_content_length < right_content_length:
            return -1
        if left_content_length > right_content_length:
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
    versions.sort(cmp=compare_version_metadata)

    # ====================================================================
    # now we'll exclude versions which content includes few other versions
    # first we need to numerate all versions
    # logic is following;
    #

    for idx, version in enumerate(versions):
        version.id = idx

    # these are for debugging purposes
    by_number = {v.version: v
                 for v in versions}

    by_id = {v.id: v
             for v in versions}

    #print_tree(root_env)

    inclusions = defaultdict(list)

    for i in versions:
        if i.filename == 'VCS':
            continue

        for j in versions:
            if i != j:
                i_content = i.content
                j_content = j.content

                i_file_section = i.find_parent_of_type('file_section')

                if i_content and j_content \
                   and j_content in i_content \
                   and i_file_section.is_parent_for(j):
                    inclusions[i.id].append(j.id)

    to_filter_out = set()

    for key, values in inclusions.items():
        if len(values) > 2:
            # if filename has 3.1 in it, but there are versions like 3.1, 3.1.1 and 3.1.2,
            # then version bigger 3.1 should be filtered out.
            to_filter_out.add(key)

        else:
            outer_id = key
            inner_id = values[0]
            outer_number = by_id[outer_id].version
            inner_number = by_id[inner_id].version
            if outer_number == inner_number:
                # if filename has 3.1 in it, and it's content is another (single) version with number 3.1
                # then latter should be excluded as it could miss some information.
                to_filter_out.add(inner_id)
            else:
                # if filename has 3.1 in it and it's content includes a single 3.1.1 version in it
                # then 3.1 should be filtered out.
                to_filter_out.add(outer_id)


    # and filter them out
    versions = [version
                for version in versions
                if version.id not in to_filter_out]

    # and grouping them by version number
    # we leave only unique versions with maximum number of metadata

    versions = dict((version.version, version)
                    for version in versions)

    # and finally we'll prepare a list, sorted by version number
    versions = versions.values()
    versions.sort(cmp=lambda left, right: \
                  compare_version_numbers(left.version, right.version))

    # and will try to figure out if only one version has no date
    # and thus unreleased yet
    # only 5 latest versions take a part in this calculations
    without_date = [version
                    for version in versions[-5:]
                    if getattr(version, 'date', None) is None]

    # if there is at least 2 versions with dates, then
    # consider version without date as unreleased
    if len(without_date) == 1 and len(versions[-5:]) >= 3:
        without_date[0].unreleased = True

    return versions



# file|parse -> sections|filter_versions -> create_raw_versions|sort
