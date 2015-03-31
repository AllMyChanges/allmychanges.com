# coding: utf-8
import arrow
import os
import re
import string
import envoy
import logging
import graphitesend
import time
import times
import threading
import lxml

from lxml import html
from contextlib import contextmanager
from functools import wraps

from django.conf import settings
from django.utils.encoding import force_text


MINUTE = 60
HOUR = 60 * MINUTE

def load_data(filename):
    data = []
    with open(filename) as f:
        for line in f.readlines():
            data.append(
                tuple(map(string.strip, line.split(';', 1))))

    return data


def first(iterable, default=None):
    """Returns first item or `default`."""
    if hasattr(iterable, 'all'):
        iterable = iterable.all()

    iterator = iter(iterable)
    try:
        return iterator.next()
    except StopIteration:
        return default


# all parts of code which needs to change
# current directory, should be serialized
# to not interfere with each other
_cd_lock = threading.RLock()

@contextmanager
def cd(path):
    """Usage:

    with cd(to_some_dir):
        envoy.run('task do')
    """
    _cd_lock.acquire()
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)
        _cd_lock.release()


def get_package_metadata(path, field_name):
    """Generates PKG-INFO and extracts given field.
    Example:
    get_package_metadata('/path/to/repo', 'Name')
    """
    with cd(path):
        response = envoy.run('python setup.py egg_info')
        for line in response.std_out.split('\n'):
            if 'PKG-INFO' in line:
                with open(line.split(None, 1)[1]) as f:
                    text = f.read()
                    match = re.search(r'^{0}: (.*)$'.format(field_name),
                                      text,
                                      re.M)
                    if match is not None:
                        return match.group(1)




def get_markup_type(filename):
    """Return markdown or rest or None"""
    extension = filename.rsplit('.', 1)[-1].lower()
    mapping = dict(
        markdown={'md', 'markdown', 'mdown'},
        rest={'rst', 'rest'},
    )
    for markup_type, possible_extensions in mapping.items():
        if extension in possible_extensions:
            return markup_type



def get_clean_text_from_html(raw_html):
    if not raw_html:
        return ''
    return html.tostring(html.fromstring(force_text(raw_html)),
                         method='text', encoding=unicode)


def get_clean_text_from_markup_text(text, markup_type):
    raw_html = _render_text_for_markup_type(text, markup_type=markup_type)
    return get_clean_text_from_html(raw_html)


def _render_text_for_markup_type(text, markup_type):
    if markup_type == 'markdown':
        return _render_markdown(text)
    elif markup_type == 'rest':
        return _render_rest(text)
    else:
        return text


def _render_markdown(text):
    if text is None:
        text = ''
    return markup.markdown(force_text(text))


def _render_rest(text):
    if text is None:
        text = ''
    return markup.restructuredtext(force_text(text))


def get_change_type(text):
    """Return new or fix or None"""
    text = text.lower()

    if re.search(r'cve-\d+-\d+', text) is not None:
        return 'sec'
    elif 'backward incompatible' in text:
        return 'inc'
    elif 'deprecated' in text:
        return 'dep'
    elif text.startswith('add'):
        return 'new'
    elif text.startswith('new '):
        return 'new'
    elif '[new]' in text:
        return 'new'
    elif text.startswith('fix'):
        return 'fix'
    elif ' fixes' in text:
        return 'fix'
    elif ' fixed' in text:
        return 'fix'
    elif 'bugfix' in text:
        return 'fix'
    elif 'bug' in text:
        return 'fix'
    elif '[fix]' in text:
        return 'fix'
    return 'new'


def graphite_send(**kwargs):
    try:
        g = graphitesend.init(prefix=settings.GRAPHITE_PREFIX,
                              system_name='',
                              graphite_server=settings.GRAPHITE_HOST)
        g.send_dict(kwargs)
    except Exception:
        logging.getLogger('django').exception('Graphite is down')


def count(metric_key, value=1):
    """Log some metrics to process with logster and graphite."""
    logging.getLogger('stats').info(
        'METRIC_COUNT metric={metric} value={value}'.format(
            metric=metric_key, value=value))


@contextmanager
def count_time(metric_key):
    """Log some timings to process with logster and graphite."""
    start = time.time()
    try:
        yield
    finally:
        value = time.time() - start
        logging.getLogger('stats').info(
            'METRIC_TIME metric={metric} value={value}s'.format(
                metric=metric_key, value=value))


def show_debug_toolbar(request):
    return True


def discard_seconds(dt):
    dt = arrow.get(dt)
    dt = dt.replace(second=0, microsecond=0)
    return dt.datetime


def dt_in_window(tz, system_time, hour):
    local = times.to_local(system_time, tz)
    return local.hour == hour


def parse_ints(text):
    """Parses text with comma-separated list of integers
    and returns python list of itegers."""
    return map(int, filter(None, text.split(',')))


def join_ints(ints):
    """Joins list of intergers into the ordered comma-separated text.
    """
    return ','.join(map(str, sorted(ints)))


def split_filenames(text):
    """Splits comma or newline separated filenames
    and returns them as a list.
    """
    names = [name.strip()
             for name in re.split(r'[\n,]', text)]
    return list(filter(None, names))


def strip_long_text(text, max_len, append=u'…'):
    """Returns text which len is less or equal max_len.
    If text is stripped, then `append` is added,
    but resulting text will have `max_len` length anyway.
    """
    if len(text) < max_len - 1:
        return text
    return text[:max_len - len(append)] + append


def trace(func):
    """Decorator which simple prints function calls and their results
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print 'CALL: {0}({1}, {2}) -> raise {3}'.format(
                func.__name__, args, kwargs, e)
            raise
        else:
            if 'cache' in kwargs:
                del kwargs['cache']
            print 'CALL: {0}({1}, {2}) -> returned {3}'.format(
                func.__name__, args, kwargs, result)
            return result
    return wrapper


def get_text_from_response(response):
    """Returns text from response, replacing
    default encoding with utf-8.
    we need this because when `requests` library
    unable to discover response encoding from headers,
    it pretends it is a latin-1, but many text
    on the internet now is utf-8, like
    Code's changelog for example:
    http://panic.com/jp/coda/releasenotes.html
    """
    if response.encoding == 'ISO-8859-1':
        response.encoding = 'utf-8'
    return response.text


def is_http_url(text):
    return re.match('^https?://.*$', text, flags=re.IGNORECASE) is not None

is_not_http_url = lambda text: not is_http_url(text)


def is_attr_pattern(text):
    """Attribute patters are like '[title=Version \d.*]'
    """
    return text.startswith('[')

is_not_attr_pattern = lambda text: not is_attr_pattern(text)


def html_document_fromstring(text):
    """Accepts unicode strings and uses special hack
    to make sure lxml dont find charset encoding.
    """
    # the hack :)
    match = re.search(ur'encoding=[\'"](?P<encoding>.*?)[\'"] ?\?>',
                      text[:200],
                      flags=re.IGNORECASE)
    if match is not None:
        text = text.encode(match.group('encoding'))

    return lxml.html.document_fromstring(text)


def parse_search_list(text):
    """Parses comma-separated list of patterns for search.

    Returns a list of tuples like [(pattern, markup)]
    Some patterns could http urls or [attrname=pattern].

    Http urls are used in rechttp downloader, to filter
    only needed urls.

    Attribute patterns are used to filter already processed
    versions by attribute's value, for example by title.
    """
    def process(name):
        if is_not_http_url(name) \
           and is_not_attr_pattern(name) \
           and ':' in name:
            return name.rsplit(':', 1)
        else:
            return (name, None)

    items = split_filenames(text)
    return map(process, items)


def first_sentences(text, max_length=1000):
    """Returns first sentences with cumulative length no more than max_length.
    If there is one very long sentence, then it will be cutted to max_length-1
    and ... unicode symbol will be added to the end.
    """
    text = text.replace('\n', ' ')

    if len(text) <= max_length:
        return text

    sentences = []
    regex = re.compile(ur'[.?!] +')

    pos = 0
    match = regex.search(text, pos)
    if match is None:
        return text[:max_length - 1] + u'…'

    while match is not None:
        end = match.start()
        group0 = match.group(0)

        sentence = text[pos: end] + group0.strip()
        sentences.append(sentence)
        pos = end + len(group0)

        match = regex.search(text, pos)

    last_sentence = text[pos:]
    sentences.append(last_sentence)

    first_sentence = sentences[0]
    if len(first_sentence) > max_length:
        return first_sentence[:max_length - 1] + u'…'

    sum_len = 0

    for idx, sentence in enumerate(sentences):
        sentence_len = len(sentence)
        if idx > 0:
            sentence_len += 1 # because we have to insert space between sentences

        if sum_len + sentence_len > max_length:
            return u' '.join(sentences[:idx])
        sum_len += sentence_len

    raise RuntimeError('Should never go here.')
