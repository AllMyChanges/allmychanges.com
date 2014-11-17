import anyjson
import datetime
import os
import re
import string
import envoy
import logging
import graphitesend
import time
import times
import requests

from lxml import html
from contextlib import contextmanager

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


@contextmanager
def cd(path):
    """Usage:

    with cd(to_some_dir):
        envoy.run('task do')
    """
    old_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_path)


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


def slack_send(text):
    if settings.SLACK_URL:
        requests.post(settings.SLACK_URL, data=anyjson.serialize(dict(text=text)))


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
    return datetime.datetime(*dt.timetuple()[:5])


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
