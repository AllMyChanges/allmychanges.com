# coding: utf-8
import urlparse
import anyjson
import tempfile
import re
import os.path
import shutil
import envoy
import requests
import plistlib
import lxml

from django.conf import settings
from urlparse import urlsplit
from allmychanges.utils import cd, get_text_from_response, is_http_url
from allmychanges.exceptions import DownloaderWarning
from twiggy_goodies.threading import log


def get_itunes_app_id(url):
    """Returns itunes lookup url if applicable, or None.
    """
    match = re.search(ur'id(?P<id>\d+)', url)
    if match is not None:
        app_id = match.group('id')
        return app_id


def get_itunes_app_data(app_id):
    url = 'https://itunes.apple.com/lookup?id={0}&lang=en_us'.format(app_id)
    data = requests.get(url).json()
    if data['resultCount'] > 0:
        return data['results'][0]


fronts = [
        ('Algeria', 'DZ', 143563),
        ('Angola', 'AO', 143564),
        ('Anguilla', 'AI', 143538),
        ('Antigua & Barbuda', 'AG', 143540),
        ('Argentina', 'AR', 143505),
        ('Armenia', 'AM', 143524),
        ('Australia', 'AU', 143460),
        ('Austria', 'AT', 143445),
        ('Azerbaijan', 'AZ', 143568),
        ('Bahrain', 'BH', 143559),
        ('Bangladesh', 'BD', 143490),
        ('Barbados', 'BB', 143541),
        ('Belarus', 'BY', 143565),
        ('Belgium', 'BE', 143446),
        ('Belize', 'BZ', 143555),
        ('Bermuda', 'BM', 143542),
        ('Bolivia', 'BO', 143556),
        ('Botswana', 'BW', 143525),
        ('Brazil', 'BR', 143503),
        ('British Virgin Islands', 'VG', 143543),
        ('Brunei', 'BN', 143560),
        ('Bulgaria', 'BG', 143526),
        ('Canada', 'CA', 143455),
        ('Cayman Islands', 'KY', 143544),
        ('Chile', 'CL', 143483),
        ('China', 'CN', 143465),
        ('Colombia', 'CO', 143501),
        ('Costa Rica', 'CR', 143495),
        ('Cote D\'Ivoire', 'CI', 143527),
        ('Croatia', 'HR', 143494),
        ('Cyprus', 'CY', 143557),
        ('Czech Republic', 'CZ', 143489),
        ('Denmark', 'DK', 143458),
        ('Dominica', 'DM', 143545),
        ('Dominican Rep.', 'DO', 143508),
        ('Ecuador', 'EC', 143509),
        ('Egypt', 'EG', 143516),
        ('El Salvador', 'SV', 143506),
        ('Estonia', 'EE', 143518),
        ('Finland', 'FI', 143447),
        ('France', 'FR', 143442),
        ('Germany', 'DE', 143443),
        ('Ghana', 'GH', 143573),
        ('Greece', 'GR', 143448),
        ('Grenada', 'GD', 143546),
        ('Guatemala', 'GT', 143504),
        ('Guyana', 'GY', 143553),
        ('Honduras', 'HN', 143510),
        ('Hong Kong', 'HK', 143463),
        ('Hungary', 'HU', 143482),
        ('Iceland', 'IS', 143558),
        ('India', 'IN', 143467),
        ('Indonesia', 'ID', 143476),
        ('Ireland', 'IE', 143449),
        ('Israel', 'IL', 143491),
        ('Italy', 'IT', 143450),
        ('Jamaica', 'JM', 143511),
        ('Japan', 'JP', 143462),
        ('Jordan', 'JO', 143528),
        ('Kazakstan', 'KZ', 143517),
        ('Kenya', 'KE', 143529),
        ('Korea, Republic Of', 'KR', 143466),
        ('Kuwait', 'KW', 143493),
        ('Latvia', 'LV', 143519),
        ('Lebanon', 'LB', 143497),
        ('Liechtenstein', 'LI', 143522),
        ('Lithuania', 'LT', 143520),
        ('Luxembourg', 'LU', 143451),
        ('Macau', 'MO', 143515),
        ('Macedonia', 'MK', 143530),
        ('Madagascar', 'MG', 143531),
        ('Malaysia', 'MY', 143473),
        ('Maldives', 'MV', 143488),
        ('Mali', 'ML', 143532),
        ('Malta', 'MT', 143521),
        ('Mauritius', 'MU', 143533),
        ('Mexico', 'MX', 143468),
        ('Moldova, Republic Of', 'MD', 143523),
        ('Montserrat', 'MS', 143547),
        ('Nepal', 'NP', 143484),
        ('Netherlands', 'NL', 143452),
        ('New Zealand', 'NZ', 143461),
        ('Nicaragua', 'NI', 143512),
        ('Niger', 'NE', 143534),
        ('Nigeria', 'NG', 143561),
        ('Norway', 'NO', 143457),
        ('Oman', 'OM', 143562),
        ('Pakistan', 'PK', 143477),
        ('Panama', 'PA', 143485),
        ('Paraguay', 'PY', 143513),
        ('Peru', 'PE', 143507),
        ('Philippines', 'PH', 143474),
        ('Poland', 'PL', 143478),
        ('Portugal', 'PT', 143453),
        ('Qatar', 'QA', 143498),
        ('Romania', 'RO', 143487),
        ('Russia', 'RU', 143469),
        ('Saudi Arabia', 'SA', 143479),
        ('Senegal', 'SN', 143535),
        ('Serbia', 'RS', 143500),
        ('Singapore', 'SG', 143464),
        ('Slovakia', 'SK', 143496),
        ('Slovenia', 'SI', 143499),
        ('South Africa', 'ZA', 143472),
        ('Spain', 'ES', 143454),
        ('Sri Lanka', 'LK', 143486),
        ('St. Kitts & Nevis', 'KN', 143548),
        ('St. Lucia', 'LC', 143549),
        ('St. Vincent & The Grenadines', 'VC', 143550),
        ('Suriname', 'SR', 143554),
        ('Sweden', 'SE', 143456),
        ('Switzerland', 'CH', 143459),
        ('Taiwan', 'TW', 143470),
        ('Tanzania', 'TZ', 143572),
        ('Thailand', 'TH', 143475),
        ('The Bahamas', 'BS', 143539),
        ('Trinidad & Tobago', 'TT', 143551),
        ('Tunisia', 'TN', 143536),
        ('Turkey', 'TR', 143480),
        ('Turks & Caicos', 'TC', 143552),
        ('Uganda', 'UG', 143537),
        ('UK', 'GB', 143444),
        ('Ukraine', 'UA', 143492),
        ('United Arab Emirates', 'AE', 143481),
        ('Uruguay', 'UY', 143514),
        ('USA', 'US', 143441),
        ('Uzbekistan', 'UZ', 143566),
        ('Venezuela', 'VE', 143502),
        ('Vietnam', 'VN', 143471),
        ('Yemen', 'YE', 143571),
]

_country_to_front = dict((item[0], item)
                     for item in fronts)
_try_fronts = [
    _country_to_front['USA'],
    _country_to_front['UK'],
    _country_to_front['Russia'],
] + fronts


def get_itunes_release_notes(app_id, fronts=_try_fronts):
    if not fronts:
        return None
    country, country_code, front = fronts[0]

    with log.name_and_fields('itunes', front=front, country=country):
        url = 'https://itunes.apple.com/app/id{0}?mt=8'.format(app_id)
        headers = {'X-Apple-Store-Front': '{0}-2,28'.format(front)}
        response = requests.get(url, headers=headers)
        if response.status_code == 400:
            return get_itunes_release_notes(app_id, fronts=fronts[1:])

        ctype = response.headers.get('content-type', '').split(';')[0].strip()
        if ctype == 'text/xml':
            data = plistlib.readPlistFromString(get_text_from_response(response))
            if data.get('m-allowed') is False:
                return get_itunes_release_notes(app_id, fronts=fronts[1:])
        else:
            page = get_text_from_response(response)
            data = re.sub(ur'.*its.serverData=(?P<data>.*?)</.*',
                          ur'\g<data>',
                          page,
                          flags=re.DOTALL)
            data = anyjson.deserialize(data)
            return data


def normalize_url(url, for_checkout=True):
    """Normalize url either for browser or for checkout.
    Usually, difference is in the schema.
    It normalizes url to 'git@github.com:{username}/{repo}' and also
    returns username and repository's name.
    """
    for_browser = not for_checkout
    github_template = 'git://github.com/{username}/{repo}'
    bitbucket_template = 'https://bitbucket.org/{username}/{repo}'

    if for_browser:
        github_template = 'https://github.com/{username}/{repo}'

    url = url.replace('git+', '')

    if 'github' in url:
        regex = r'github.com[/:](?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]+?)(?:\.git$|/$|/tree/master$|$)'
        match = re.search(regex, url)
        if match is None:
            # some url to a raw file or github wiki
            return (url, None, None)
        else:
            username, repo = match.groups()
            return (github_template.format(**locals()),
                    username,
                    repo)


    elif 'bitbucket' in url:
        regex = r'bitbucket.org/(?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]*)'
        username, repo = re.search(regex, url).groups()
        return (bitbucket_template.format(**locals()),
                username,
                repo)
    elif 'itunes.apple.com' in url:
        app_id = get_itunes_app_id(url)
        data = get_itunes_app_data(app_id)
        if data:
            # here we add iTunes Affilate token
            return (data['trackViewUrl'] + '&at=1l3vwNn', None, None)

    return (url, None, url.rsplit('/')[-1])



def download_repo(url, pull_if_exists=True):
    url, username, repo = normalize_url(url)

    path = os.path.join(settings.REPO_ROOT, username, repo)

    if os.path.exists(os.path.join(path, '.failed')):
        return None

    if os.path.exists(path):
        if pull_if_exists:
            with cd(path):
                response = envoy.run('git checkout master')
                if response.status_code != 0:
                    raise RuntimeError(
                        'Bad status_code from git checkout master: '
                        '{0}. Git\'s stderr: {1}'.format(
                            response.status_code, response.std_err))

                response = envoy.run('git pull')
                if response.status_code != 0:
                    raise RuntimeError('Bad status_code from git pull: '
                                       '{0}. Git\'s stderr: {1}'.format(
                                           response.status_code,
                                           response.std_err))
    else:
        response = envoy.run('git clone {url} {path}'.format(url=url,
                                                             path=path))

        if response.status_code != 0:
            os.makedirs(path)
            with open(os.path.join(path, '.failed'), 'w') as f:
                f.write('')
            raise RuntimeError('Bad status_code from git clone: {0}. '
                               'Git\'s stderr: {1}'.format(
                                   response.status_code, response.std_err))

    return path


def fake_downloader(source,
                    search_list=[],
                    ignore_list=[]):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)

    source = source.replace('test+', '')

    if os.path.isfile(source):
        shutil.copyfile(
            source,
            os.path.join(path, 'CHANGELOG'))
        return path
    else:
        destination = os.path.join(path, 'project')
        shutil.copytree(source, destination)
        return destination


def split_branch(url):
    if '@' in url:
        return url.split('@', 1)
    return url, None


def git_downloader(source,
                   search_list=[],
                   ignore_list=[]):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url, username, repo_name = normalize_url(source)

    url, branch = split_branch(url)

    with cd(path):
        response = envoy.run('git clone {url} {path}'.format(url=url,
                                                             path=path))
        if response.status_code != 0:
            if os.path.exists(path):
                shutil.rmtree(path)
            raise RuntimeError('Bad status_code from git clone: {0}. '
                               'Git\'s stderr: {1}'.format(
                                   response.status_code, response.std_err))

        if branch:
            response = envoy.run('git checkout -b {branch} origin/{branch}'.format(branch=branch))

            if response.status_code != 0:
                if os.path.exists(path):
                    shutil.rmtree(path)
                raise RuntimeError('Bad status_code from git checkout -b {0}: {1}. '
                                   'Git\'s stderr: {2}'.format(
                                       branch, response.status_code, response.std_err))

    return path

def hg_downloader(source,
                  search_list=[],
                  ignore_list=[]):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = source.replace('hg+', '')

    with cd(path):
        response = envoy.run('hg clone {url} {path}'.format(url=url,
                                                             path=path))
    if response.status_code != 0:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise RuntimeError('Bad status_code from hg clone: {0}. '
                           'Mercurial\'s stderr: {1}'.format(
                               response.status_code, response.std_err))

    return path


def http_downloader(source,
                    search_list=[],
                    ignore_list=[]):
    path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    url = source.replace('http+', '')

    try:
        with cd(path):
            response = requests.get(url)
            with open('ChangeLog', 'w') as f:
                f.write(get_text_from_response(response).encode('utf-8'))

    except Exception, e:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise RuntimeError('Unexpected exception "{0}" when fetching: {1}'.format(
            e, url))
    return path


def itunes_downloader(source,
                      search_list=[],
                      ignore_list=[]):
    """Processes iOS app's changelog from urls like these
    https://itunes.apple.com/in/app/temple-run/id420009108?mt=8
    https://itunes.apple.com/en/app/slack-team-communication/id618783545?l=en&mt=8
    """
    app_id = get_itunes_app_id(source)
    data = get_itunes_release_notes(app_id)
    history = data['pageData']['softwarePageData']['versionHistory']
    if history:
        def format_item(item):
            version = item['versionString']
            date = item['releaseDate']
            notes = item.get('releaseNotes') or 'No description'
            notes = notes.replace(u'•', u'*') # because of vk.com mothefuckers
            notes = notes.replace(u'★', u'*') # because of temple run motherfuckers
            text = u"""
{version} ({date})
==============

{notes}
            """.strip().format(version=version,
                               date=date,
                               notes=notes)
            return text

        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
        try:
            with cd(path):
                with open('ChangeLog', 'w') as f:
                    items = map(format_item, history)
                    text = u'\n\n'.join(items)
                    f.write(text.encode('utf-8'))

        except Exception, e:
            if os.path.exists(path):
                shutil.rmtree(path)
            raise RuntimeError('Unexpected exception "{0}" when fetching itunes app: {1}'.format(
                repr(e), app_id))
        return path


def rechttp_downloader(source,
                       search_list=[],
                       ignore_list=[]):
    base_path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
    base_url = source.replace('rechttp+', '')
    queue = [base_url]
    already_seen = set()

    search_list = [item
                   for item, parser_name in search_list
                   if is_http_url(item)]
    if search_list:
        limit_urls = 100
        search_patterns = [('^' + item + '$')
                           for item in search_list]
    else:
        limit_urls = 10
        if base_url.endswith('/'):
            search_patterns = ['^' + base_url + '.*$']
        else:
            search_patterns = ['^' + base_url.rsplit('/', 1)[0] + '/.*$']

    search_patterns = map(re.compile, search_patterns)

    def pass_filters(link):
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
        if path.endswith('/'):
            path += 'index.html'
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
        response = requests.get(url)
        filename = filename_from(response)
        fs_path = os.path.join(base_path, filename)
        ensure_dir(os.path.dirname(fs_path))

        text = get_text_from_response(response)

        if response.headers['content-type'].startswith(
            'text/html'):
            tree = lxml.html.document_fromstring(text)

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

        if len(already_seen) == limit_urls:
            raise DownloaderWarning('Please, specify one or more URL patterns in search list. Use regexes.')

    except DownloaderWarning:
        raise
    except Exception, e:
        if os.path.exists(base_path):
            shutil.rmtree(base_path)
        raise RuntimeError('Unexpected exception "{0}" when fetching: {1}'.format(
            e, url))
    return base_path



def guess_downloader(url):
    parts = urlsplit(url)

    if parts.hostname == 'itunes.apple.com':
        return 'itunes'

    if parts.hostname == 'github.com':
        url, username, repo = normalize_url(url)
        if username and repo:
            # then we sure it is a git repo
            # otherwise, we have to try downloaders one after another
            return 'git'

    if url.startswith('test+'):
        return 'fake'

    if url.startswith('rechttp+'):
        return 'rechttp'

    downloaders = [('git', git_downloader),
                   ('hg', hg_downloader),
                   ('http', http_downloader)]

    for name, downloader in downloaders:
        try:
            path = downloader(url)
            shutil.rmtree(path)
            return name
        except Exception:
            pass

    return None


def get_downloader(name):
    return globals().get(name + '_downloader')
