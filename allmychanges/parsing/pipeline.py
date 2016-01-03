# coding: utf-8
import re
import codecs
import os
import tempfile
import shutil
import envoy
import lxml.html

from lxml import etree
from operator import itemgetter
from collections import defaultdict
from functools import wraps
from itertools import takewhile, islice
from pkg_resources import parse_version
from rq.timeouts import JobTimeoutException
from django.utils.encoding import force_text

from allmychanges.crawler import (
    _extract_version, _extract_date,
    _parse_item)
from allmychanges.markdown import render_markdown
from allmychanges.utils import (
    strip_long_text, is_not_http_url,
    is_http_url, is_attr_pattern,
    html_document_fromstring)
from allmychanges.parsing.unreleased import mention_unreleased
from allmychanges.parsing.postprocessors import sed
from allmychanges.env import Environment, deserialize_envs
from django.conf import settings
from twiggy_goodies.threading import log


CHANGELOG_LIKE_FILENAMES = ('change', 'release', 'news', 'history')
EXTENSIONS_TO_CHECK = {'.rst', '.md', '.markdown', '.txt', '.htm', '.html'}


def filename_looks_like_a_changelog(filename):
    filename = filename.lower()
    return any((item in filename)
               for item in CHANGELOG_LIKE_FILENAMES)


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

    ignore_list = [re.compile('^' + item + '.*$')
                   for item in env.ignore_list
                   if not (is_http_url(item) or is_attr_pattern(item))]
    search_list = [(re.compile('^' + item + '.*$'), markup)
                   for item, markup in env.search_list
                   if not (is_http_url(item) or is_attr_pattern(item))]

    def in_ignore_list(filename):
        for pattern in ignore_list:
            if pattern.match(filename) is not None:
                return True
        return False

    def search_in_search_list(filename):
        for pattern, markup in search_list:
            if pattern.match(filename) is not None:
                return True, markup
        return False, None

    saved_env_file = os.path.join(env.dirname, 'versions.amchenvs')

    if os.path.exists(saved_env_file):
        # if we have already processed environment
        # then will read only this file
        yield env.push(type='filename',
                       filename=saved_env_file,
                       markup='amchenvs')
        return

    for root, dirs, files in walk(env.dirname):
        root = force_text(root)
        for filename in files:
            filename = force_text(filename)
            full_filename = os.path.join(root, filename)
            rel_filename = os.path.relpath(full_filename, env.dirname)

            low_filename = rel_filename.lower()
            _, ext = os.path.splitext(low_filename)

            with log.name_and_fields('get_files',
                                     filename=rel_filename):
                # TODO: перенести эту проверку внутрь за ignore и search
                if ext not in EXTENSIONS_TO_CHECK \
                   and not filename_looks_like_a_changelog(low_filename):
#                    log.debug('Skipped because extension not in ' + ','.join(EXTENSIONS_TO_CHECK))
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
                            log.debug('Skipped because not match to search list.')

                    else:
                        yield env.push(**attrs)
                else:
                    log.debug('Skipped because matches to ignore list.')


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


def parse_amchenvs_file(obj):
    return deserialize_envs(obj.content)


def parse_markdown_file(obj):
    content = obj.content

    postprocessor_template = getattr(obj, 'xslt', None)
    if postprocessor_template:
        transform = sed(postprocessor_template)
        content = transform(content)

    html = render_markdown(content)
    # import markdown2
    # html = markdown2.markdown(obj.content)

    return parse_html_file(obj.push(content=html))


def parse_plain_file(obj):
    current_title = None
    current_title_ident = 0
    # here we'll track each line distance from corresponding
    # line with version number
    current_sections = []
    current_section = None
    current_ident = None
    content = obj.content

    def format_section(section):
        if isinstance(section, list):
            return messages_to_html(section)
        return u'<p>{0}</p>'.format(section)

    def format_content(sections):
        return u'\n'.join(map(format_section, sections))

    postprocessor_template = getattr(obj, 'xslt', None)
    if postprocessor_template:
        transform = sed(postprocessor_template)
        content = transform(content)

    for line in content.split('\n'):
        # skip lines like
        # ===================
        if line and line == line[0] * len(line):
            continue

        is_item, ident, text = _parse_item(line)

        # ищем версию только
        # если строка не элемент списка и сам
        # список внутри потенциальной версии
        # (is_item или ident) указывают на то,
        # что строка является либо началом, либо следующей
        # строкой элемента списка, как в nodejs 0.1.4
        version = _extract_version(line)
        if current_title:
            if ident and ident > current_title_ident:
                version = None

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
                current_title_ident = ident
                current_section = None
                current_sections = []
                current_ident = None

            elif ident >= current_ident and isinstance(current_section, list):
                # previous changelog item has continuation on the
                # next line
                current_section[-1] += '<br/>' + line[current_ident:]
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
                        current_section += u'<br/>' + line

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
            content = obj.content

            postprocessor_template = getattr(obj, 'xslt', None)
            if postprocessor_template:
                transform = sed(postprocessor_template)
                content = transform(content)

            with codecs.open(os.path.join(path, 'index.rst'), 'w', 'utf-8') as f:
                f.write(content)

            envoy.run('rm -fr {0}/output/index.html'.format(path))
            command = 'sphinx-build -b html {0} {0}/output'.format(path)
            response = envoy.run(command)

            if os.environ.get('SET_TRACE'):
                import pdb; pdb.set_trace()

            if response.status_code != 0:
                log.error('Bad status code from sphinx-build:\n{0}\n{1}'.format(
                    command, response.std_err))

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

XPath = lxml.html.etree.XPath
XPATHS_TO_CUT_FROM_HTML = [
    XPath('//*[contains(@class, "footer")]'),
    XPath('//*[contains(@class, "related-links")]'),
    XPath('//*[@id="footer"]'),
]

def parse_html_file(obj):
    """
    Uses fields `content` and `filename` to generate new file_sections.
    """
    if not obj.content:
        # Some files are empty, document_fromstring raises exception on them
        return

    try:
        parsed = html_document_fromstring(obj.content)
        xslt = getattr(obj, 'xslt', None)

        if xslt and xslt[0] == '<':
            transform = etree.XSLT(etree.XML(xslt))
            parsed = transform(parsed)

        for xpath in XPATHS_TO_CUT_FROM_HTML:
            elems = xpath(parsed)
            for el in elems:
                el.drop_tree()
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
        return u''.join(strings).strip()


    def header_level(element):
        depth = 0
        el = element
        path = []
        while el is not None:
            el = el.getparent()
            path.insert(0, getattr(el, 'tag', None))
            depth += 1

        default_h_level = 1000
        h_levels = {
            'body': 0,
            'h1': 1, 'h2': 2,
            'h3': 3, 'h4': 4,
            'h5': 5, 'h6': 6}
        h_level = h_levels.get(
            element.tag,
            default_h_level)

        return depth, h_level

    headers = [(header_level(el),
                el,
                el.text_content().strip(),
                el.itersiblings())
               for el in headers]

    body = parsed.find('body')
    if body is not None:
        headers.insert(0, (header_level(body),
                           body,
                           obj.filename,
                           body.iterchildren()))

    def process_header(parent, level, elem, title, all_children):
        def not_same_level_H(ch):
            if isinstance(ch.tag, basestring):
                return not ch.tag.lower().startswith('h') \
                    or header_level(ch) > level
            return True

        children = list(takewhile(
            not_same_level_H,
            all_children))

        full_content = create_full_content(children)

        return parent.push(type='file_section',
                           title=title,
                           content=full_content)

    stack = [((-1, 1), obj)]

    for h_level, h_elem, h_title, h_children in headers:
        # now,remove deeper headers fromtop of the stack
        while stack[-1][0] >= h_level:
            stack.pop()

        result_item = process_header(stack[-1][1],
                                     h_level,
                                     h_elem,
                                     h_title,
                                     h_children)
        stack.append((h_level, result_item))
        yield result_item


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
    first_lines = (line for line in version.content.split(u'\n', 10))
    first_lines = (line[:200] for line in first_lines)
    first_lines = (line.strip() for line in first_lines)
    first_lines = (line for line in first_lines if line)
    first_lines = list(islice(first_lines, 0, 3))

    first_lines.insert(0, version.title)

    new_version = version.push(type='prerender_items')
    for line in first_lines:
        date = _extract_date(line)
        if date:
            new_version.date = date
            break
        if mention_unreleased(line):
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
        check(ur'breaking changes?', u'fix'),

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


def process_version_description(html):
    """Processes html, sanitizing and adding additional markup.
    """
    from ..templatetags.allmychanges_tags import process_cve
    from django.template.defaultfilters import capfirst
    from bleach import clean

    def remove_html_markup(text, *args, **kwargs):
        # removing reST's fucking field-list from our nice changelog item
        text = re.sub(ur'<table class="docutils field-list".*?</table>', u'', text, flags=re.DOTALL | re.M)

        def filter_div_attrs(name, value):
            if name == 'style' and value == 'display: none':
                return True
            return False

        text = clean(text,
                     tags=[u'table', 'colgroup', 'col', 'tr', 'td', 'th', 'tbody', 'thead',
                           u'a', u'abbr', u'acronym', u'b', u'blockquote',
                           u'code', u'em', u'i', u'li', u'ol', u'strong', u'ul', # these are default
                           u'dl', u'dt', u'dd', # allow definition lists
                           u'p', # we allow paragraphs cause they are fine
                           u'article', # эти теги добавляются github release даунлоадером
                           u'h1', u'h2', u'h3', u'h4', u'h5', # headers are ok too
                           u'del', u'strike', u's',
                           u'tt', # monospace
                           u'div', # dont see why it should be prohibited
                           u'span', # and spans too
                           u'pre', u'cite', u'samp', u'kbd',
                           u'str', # this is nonstandart, but used in Cloudera's docs
                           u'img', # images are nice
                           u'video', u'object', u'embed', u'param', # videos are ok too
                           u'br', # allow linebreaks because they are generated by VCS extractor.
                       ],
                     attributes={u'a': [u'href', u'title'],
                                 u'acronym': [u'title'],
                                 u'img': [u'src', u'width', u'height', u'title'],
                                 u'abbr': [u'title'],
                                 u'video': [u'width', u'height', u'controls', u'src'],
                                 u'object': [u'width', u'height', u'classid', u'codebase'],
                                 u'embed': [u'width', u'height', u'type', u'src', u'flashvars'],
                                 u'param': [u'name', u'value'],
                                 u'div': filter_div_attrs},
                     styles=['display']) # NEVER ALLOW STYLE attribute without additional checking for style value
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

    return apply_filters(html)


def update_version_content(version):
    # TODO: remove after all versions will be converted
    if version.processed_text:
        return False

    content = []
    for section in version.sections.all():
        if section.notes:
            content.append(section.notes)
        else:
            messages = [item.text for item in section.items.all()]
            messages = [re.sub(ur'<span class="changelog-item.*?</span>', '', text)
                        for text in messages]
            content.append(messages_to_html(messages))
    content = u'\n'.join(content)
    version.raw_text = content
    version.processed_text = process_version_description(content)
    version.save(update_fields=('raw_text', 'processed_text'))
    return True

def prerender_items(version):
    processed_content = process_version_description(version.content)
    new_version = version.push(
        type='version',
        processed_content=processed_content)
    yield new_version


def group_by_path(versions):
    """ Returns a dictionary, where keys are a strings
    with directories, starting from '.' and values
    are lists with all versions found inside this directory.
    """
    make_obj = lambda: {'score': 0, 'versions': []}
    result = defaultdict(make_obj)

    for score, version in versions:
        path = version.filename.split(u'/')
        path = [name + u'/'
                for name in path[:-1]] + path[-1:]

        depth = 0
        while path:
            result[''.join(path)]['score'] += score - depth
            result[''.join(path)]['versions'].append(version)
            path = path[:-1]
            depth += 1
    return result



def filter_versions_by_attribute(versions, search_list=[], ignore_list=[]):
    pattern = re.compile(ur'\[(?P<attribute>.+)=(?P<pat>.*)\]')
    search_patterns = list(pattern.match(item[0]) for item in search_list)
    search_patterns = [(match.group('attribute'), re.compile(match.group('pat')))
                       for match in search_patterns if match is not None]

    ignore_patterns = (pattern.match(item) for item in ignore_list)
    ignore_patterns = [(match.group('attribute'), re.compile(match.group('pat')))
                       for match in ignore_patterns if match is not None]

    def not_to_ignore(version):
        for attribute, pattern in ignore_patterns:
            value = getattr(version, attribute, '')
            if pattern.match(value) is not None:
                return False
        return  True

    def in_search(version):
        if search_patterns:
            for attribute, pattern in search_patterns:
                value = getattr(version, attribute, '')
                if pattern.match(value) is not None:
                    return True
            return False
        return  True

    new = [v
           for v in versions
           if in_search(v) and not_to_ignore(v)]
    return new


def filter_versions_by_source(versions):
    if not versions:
        return versions

    def calc_score(version):
        if filename_looks_like_a_changelog(version.filename):
            return 1000
        return 10

    scored = [(calc_score(version), version)
              for version in versions]
    grouped = group_by_path(scored)

    sources = grouped.items()
    sources.sort(reverse=True, key=lambda item: item[1]['score'])
    best_source = sources[0][0]

    log.debug('Best source was choosen: ' + best_source)
    return grouped[best_source]['versions']


def filter_versions(versions):
    result = []
    excluded = set()

    def log_excluded(s, reason):
        with log.name_and_fields('filter_versions',
                                 title=s.title,
                                 version=s.version):
            log.debug(reason)

    # для начала, пропишем номера версий всем окружениям типа file_section
    for v in versions:
        file_section = v.find_parent_of_type('file_section')
        if file_section:
            file_section.version = v.version

    for v in versions:
        file_section = v.find_parent_of_type('file_section')
        # if v.version == '2.74':
        #     # print_tree(v)

        if file_section: # if not, then this is probably from VCS
            children = file_section.get_children()
            # предварительно выберем детей, к которых такая же версия
            # если они есть, то понадобятся дельше
            same_ver_children = [item
                                 for item in children
                                 if item.type == 'file_section'
                                 and item.version == v.version]
            # а тут нам нужны только дети типа file_section
            # и у которых номера версий отличаются от текущей
            children = [item
                        for item in children
                        if item.type == 'file_section'
                           and item.version != v.version]
            # если v это 1.0 а дети: 1.0.1, 1.0.2 и т.д.
            children_versions = [ch.version for ch in children]
            if children and all(chv.startswith(v.version)
                                for chv in children_versions):
                log_excluded(v, 'Excluded because has children: ' + ', '.join(children_versions))
                excluded.add(id(file_section))
                continue

            # если есть потомок с такой же версией, и он когда-то
            # был исключен, то и этот узел надо исключить.
            # такое случается, когда 1.2 содержит 1.2 а тот содержит 1.2.1, 1.2.3...
            if same_ver_children and any(id(ch) in excluded
                                         for ch in same_ver_children):
                log_excluded(v, 'Excluded because has child with same version which was excluded in it\'s turn')
                excluded.add(id(file_section))
                continue

            parent = file_section.get_parent()
            parent_version = getattr(parent, 'version', None)
            # если нашли 2.6 внутри 1.3
            # или нашли 1.3 внутри 1.3
            if parent_version and (not v.version.startswith(parent_version) \
                                   or v.version == parent_version):
                # в этом случае, не добавляем версию в excluded,
                # иначе такую же версию верхнего уровня тоже исключим
                log_excluded(v, 'Excluded because parent version is ' + parent_version)
                continue

        result.append(v)
    return result



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


def print_tree(env):
    """Output env tree for debugging puppose.
    """
    highlight_env = env
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

        version = getattr(env, 'version', None)
        if version:
            comment += ' version=' + version

        if env is highlight_env:
            comment += ' <----------------'

        print u'{padding}{t} {comment}'.format(
            padding=u' ' * padding * 2,
            t=t,
            comment=comment)
        for child in env._children:
            child = child()
            if child is not None:
                print_env(child, padding + 1)
    print_env(env, 0)




def _processing_pipe(processors, root, ignore_list=[], search_list=[], xslt=''):
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
    root_env.ignore_list = filter(is_not_http_url, ignore_list)
    root_env.search_list = [(item, parser_type)
                            for item, parser_type in search_list
                            if is_not_http_url(item)]
    root_env.xslt = xslt
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

    versions = filter_versions_by_attribute(versions,
                                            search_list=search_list,
                                            ignore_list=ignore_list)
    # now we'll select a source with maximum number of versions
    # but not the root directory
    versions = filter_versions_by_source(versions)

    # using customized comparison we make versions which
    # have less metadata go first
    versions.sort(cmp=compare_version_metadata)

    versions = filter_versions(versions)

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
