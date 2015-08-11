# coding: utf-8

import requests
import urlparse
import shutil
import tempfile
import os
import re
import lxml

from cgi import parse_header
from collections import defaultdict
from django.conf import settings
from allmychanges.utils import (
    cd, get_text_from_response, is_http_url,
    first_sentences,
    html_document_fromstring)
from allmychanges.exceptions import DownloaderWarning
from twiggy_goodies.threading import log


def guess(source, discovered={}):
    # we don't want use HTML downloader for direct
    # Rss/Atom urls
    if 'feed' in discovered \
       and discovered['feed']['changelog']['source'] == source:
        return

    result = defaultdict(dict)
    path = ''
    try:
        path = download(source, only_one=True)
        # if everything is OK, start populating result
        result['changelog']['source'] = source
        result['params']['only_one'] = True

    except:
        # ignore errors because most probably, they are from git command
        # which won't be able to clone repository from strange url
        pass
    finally:
        if os.path.exists(path):
            shutil.rmtree(path)

    return result


def download(source,
             search_list=[],
             ignore_list=[],
             only_one=False):
    """
    Param `only_one` needed to emulate http_downloader which fetches
    only one page.
    """
    DEFAULT_UPPER_LIMIT = 100
    UPPER_LIMITS = {
        'rechttp+http://www.postgresql.org/docs/devel/static/release.html': 1000,
        'rechttp+http://changelogs.ubuntu.com/changelogs/pool/main/o/openssl/': 1000,
        'rechttp+https://enterprise.github.com/releases': 1000,
        'rechttp+https://mariadb.com/kb/en/mariadb/release-notes/': 10000,
        'rechttp+https://confluence.jetbrains.com/display/TW/ChangeLog': 1000,
    }
    upper_limit = UPPER_LIMITS.get(source, DEFAULT_UPPER_LIMIT)

    base_path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    base_url = source.replace('rechttp+', '')
    queue = [base_url]
    already_seen = set()

    search_list = [item
                   for item, parser_name in search_list
                   if is_http_url(item)]
    if only_one:
        limit_urls = 1
        search_patterns = []
    else:
        if search_list:
            limit_urls = upper_limit
            search_patterns = [('^' + item + '$')
                               for item in search_list]
        else:
            limit_urls = 10
            if base_url.endswith('/'):
                search_patterns = ['^' + base_url + '.*$']
            else:
                search_patterns = ['^' + base_url.rsplit('/', 1)[0] + '/.*$']

    search_patterns = map(re.compile, search_patterns)

    ignore_patterns = filter(is_http_url, ignore_list)
    ignore_patterns.append('.*\.(tar\.gz|tar\.bz2|tgz|tbz2|rar|zip|Z)$')
    ignore_patterns = map(re.compile, ignore_patterns)

    def pass_filters(link):
        for patt in ignore_patterns:
            if patt.match(link) is not None:
                return False
        for patt in search_patterns:
            if patt.match(link) is not None:
                return True
        return False

    def ensure_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def filename_from(response):
        splitted = urlparse.urlsplit(response.url)
        path = splitted.path
        ext = os.path.splitext(path)[1]
        if re.search('\d', ext) is not None:
            # we ignore extensions with numbers because
            # most probably they are from urls like
            # http://wiki.blender.org/index.php/Dev:Ref/Release_Notes/2.57b
            ext = ''

        ctype = response.headers.get('content-type')
        if ctype:
            ctype = parse_header(ctype)[0]

        if path.endswith('/'):
            path += 'index.html'
        elif not ext:
            if ctype == 'text/html':
                path += '.html'
        return path.lstrip('/')

    def make_absolute(url, base_url):
        if is_http_url(url):
            return url
        return urlparse.urljoin(base_url, url)

    def remove_fragment(url):
        return url.split('#', 1)[0]

    def enqueue(url):
        if url not in already_seen and url not in queue:
            queue.append(url)

    def fetch_page(url):
        response = requests.get(url, headers={'User-Agent': settings.HTTP_USER_AGENT})
        filename = filename_from(response)

        if os.environ.get('DEV_DOWNLOAD', None):
            print 'Fetching', url, '->', filename

        fs_path = os.path.join(base_path, filename)
        ensure_dir(os.path.dirname(fs_path))

        text = get_text_from_response(response)

        if response.headers.get('content-type', '').startswith(
            'text/html'):
            tree = html_document_fromstring(text)
            get_links = lxml.html.etree.XPath("//a")
            for link in get_links(tree):
                url = link.attrib.get('href')
                if url:
                    url = make_absolute(url, response.url)
                    link.attrib['href'] = url
                    url = remove_fragment(url)
                    if pass_filters(url):
                        enqueue(url)
            get_images = lxml.html.etree.XPath("//img")
            for img in get_images(tree):
                src = img.attrib.get('src')
                if src:
                    src = make_absolute(src, response.url)
                    img.attrib['src'] = src

            text = lxml.html.tostring(tree)

        with open(fs_path, 'w') as f:
            f.write(text.encode('utf-8'))



    try:
        while queue and len(already_seen) < limit_urls:
            url = queue.pop()
            already_seen.add(url)
            fetch_page(url)

        if len(already_seen) == limit_urls and not only_one:
            if limit_urls == upper_limit:
                message = ('Please, specify more URL patterns '
                           'because we hit the limit ({upper_limit} '
                           'documents). Use regexes.')
            else:
                message = ('We downloaded 10 documents. '
                           'Please, specify one or more URL '
                           'patterns in search list to extend '
                           'this limit up to {upper_limit}. Use regexes.')
            raise DownloaderWarning(message.format(upper_limit=upper_limit))

    except DownloaderWarning:
        raise
    except Exception as e:
        if os.path.exists(base_path):
            shutil.rmtree(base_path)
        with log.fields(url=url):
            log.trace().error('Unexpected error when fetching data')
        raise RuntimeError('Unexpected exception "{0}" when fetching: {1}'.format(
            e, url))
    return base_path
