# coding: utf-8

import requests
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
import datetime

from lxml import html
from contextlib import contextmanager
from functools import wraps

from django.conf import settings
from django.utils.encoding import force_text
from django.utils.html import escape
from twiggy_goodies.threading import log
from django.core.urlresolvers import reverse as django_reverse


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
        response = do('python setup.py egg_info')
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
    if not request.GET.get('snap') and \
       settings.TOOLBAR_TOKEN is not None and \
       request.GET.get('toolbar') == settings.TOOLBAR_TOKEN:
        return True


def discard_seconds(dt):
    dt = arrow.get(dt)
    dt = dt.replace(second=0, microsecond=0)
    return dt.datetime


def ensure_datetime(dt):
    """Returns `datetime` object even if `date` was passed as argument.

    This function is useful for comparison in places, where we
    not sure if both arguments have same date type.
    """
    if isinstance(dt, datetime.date):
        return datetime.datetime.fromordinal(dt.toordinal())
    else:
        assert isinstance(dt, datetime.datetime)
    return dt


def ensure_has_timezone(dt):
    dt = ensure_datetime(dt)
    if dt.tzinfo is None:
        dt = arrow.get(dt)
        dt = dt.to('UTC').datetime
    return dt


def dt_in_window(tz, system_time, hour):
    local = times.to_local(system_time, tz)
    return local.hour == hour


def change_weekday(dt, weekday):
    """Returns a new dt where weekday is weekday.
    if dt.weekday is greater than weekday, then it is decreased.
    otherwise it is increased
    """
    if weekday < 0 or weekday > 6:
        raise ValueError('Argument weekday should be integer in 0-6 range')
    return dt - datetime.timedelta(dt.weekday() - weekday)


def map_days(from_date, to_date, func):
    from_date = arrow.get(from_date)
    to_date = arrow.get(to_date).replace(days=-1)
    for date in arrow.Arrow.range('day', from_date, to_date):
        yield func(date.date())

def map_pairs(a_list, func):
    """For list [1,2,3,4]
    returns: [func(1,2), func(2,3), func(3,4)]

    Works only for lists.
    """
    result = []
    if a_list:
        head_item = a_list[0]
        tail = a_list[1:]
        while tail:
            next_item = tail[0]
            result.append(func(head_item, next_item))
            head_item = next_item
            tail = tail[1:]
    return result


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
    default encoding with gussed from source or with utf-8.
    we need this because sometimes `requests` library
    when discovering response encoding from headers,
    pretends it is a latin-1, but many text
    on the internet use meta tags or just is utf-8, like
    Code's changelog for example:
    http://panic.com/jp/coda/releasenotes.html
    """
    if response.encoding == 'ISO-8859-1':
        guessed = requests.utils.get_encodings_from_content(response.content)
        if guessed:
            response.encoding = guessed[0]
        else:
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
    if isinstance(text, unicode):
        match = re.search(ur'encoding=[\'"](?P<encoding>.*?)[\'"] ?\?>',
                          text[:200],
                          flags=re.IGNORECASE)
        if match is not None:
            # for some pages, like http://www.freebsd.org/releases/10.1R/relnotes.html
            # we fail to encode text using given encoding, that is why we use
            # errors='replace' here
            text = text.encode(match.group('encoding'),
                               errors='ignore')

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
    # TODO: at some point of time, all search lists will be
    #       stored in the database as list, and this function
    #       will be removed.
    #       After the script `migrate_downloaders` running at
    #       January 2016, some downloader_settings were converted
    #       to contain search_list as a list. But after that,
    #       all these projects were paused. After saving settings,
    #       search_list is converted back to a string.
    if isinstance(text, list):
        return text

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


def update_fields(obj, **kwargs):
    """Updates only fields given in kwargs.
    """
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.save(update_fields=kwargs.keys())


def get_keys(d, *keys):
    """Takes a dict and returns a new dict
    where only given keys are present.

    If there is no some key in original dict,
    then it will be absent in the resulting dict too.
    """
    return {key: value
            for key, value in d.items()
            if key in keys}


def do(command, timeout=60):
    with log.fields(command=command):
        log.debug('Running command')
        result = envoy.run(command, timeout=timeout)#, kill_timeout=60)
        params = dict(status_code=result.status_code)
        if result.status_code != 0:
            params['std_out'] = result.std_out
            params['std_err'] = result.std_err

        with log.fields(**params):
            log.debug('Command execution was finished')
        return result


def reverse(view_name, *args, **kwargs):
    return django_reverse(view_name,
                          args=args,
                          kwargs=kwargs)


def pdb_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        import pdb; pdb.set_trace()  # DEBUG
        return func(*args, **kwargs)
    return wrapper


def project_name(ch):
    return u'{0.namespace}/{0.name}'.format(ch)


def project_html_name(ch):
    """Returns a link to the project's page.
    Project's name contains namespace and name.
    and escaped.
    """
    name = escape(project_name(ch))
    url = settings.BASE_URL + reverse('project-by-id', pk=ch.id)
    return u'<a href="{url}">{name}</a>'.format(**locals())


def project_slack_name(ch):
    """Returns a link to a project in Slack's markup.
    Project's name contains namespace and name.
    and escaped.
    """
    name = escape(project_name(ch))
    url = settings.BASE_URL + reverse('project-by-id', pk=ch.id)
    return u'<{url}|{name}>'.format(**locals())


def user_slack_name(user):
    """Returns a link to a user's profile in Slack's markup.
    """
    name = escape(user.username)
    url = settings.BASE_URL + reverse('admin-user-profile',
                                      username=user.username)
    return u'<{url}|{name}>'.format(**locals())
