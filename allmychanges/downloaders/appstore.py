# coding: utf-8

import re
import os
import anyjson
import tempfile
import requests
import shutil
import plistlib


from django.conf import settings
from collections import defaultdict
from allmychanges.utils import (
    cd,
    log,
    get_text_from_response,
    first_sentences)
from allmychanges.exceptions import AppStoreAppNotFound


def guess(source, discovered={}):
    from allmychanges.models import DESCRIPTION_LENGTH

    with log.name_and_fields('appstore', source=source):
        log.info('Guessing')

        if not 'itunes.apple.com' in source:
            return

        result = defaultdict(dict)
        try:
            app_id = get_itunes_app_id(source)
            data = get_itunes_app_data(app_id)
            # if everything is OK, start populating result
            result['changelog']['source'] = source
            result['stop'] = True

            name = data['trackName']
            name = name.split(' - ', 1)[0]
            name = name.strip()

            result['changelog'].update(dict(
                name=name,
                namespace='ios',
                description=first_sentences(data['description'],
                                            DESCRIPTION_LENGTH)))
        except Exception:
            # ignore errors because most probably, they are from git command
            # which won't be able to clone repository from strange url
            pass

        return result


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


def get_itunes_app_id(url):
    """Returns itunes lookup url if applicable, or None.
    """
    match = re.search(ur'id(?P<id>\d+)', url)
    if match is not None:
        app_id = match.group('id')
        return app_id


def get_itunes_app_data(app_id):
    url = 'https://itunes.apple.com/lookup?id={0}&lang=en_us'.format(app_id)
    response = requests.get(url)
    data = response.json()
    if data['resultCount'] > 0:
        return data['results'][0]
    else:
        raise AppStoreAppNotFound(app_id)



def get_itunes_release_notes(app_id, fronts=_try_fronts):
    if not fronts:
        return None
    country, country_code, front = fronts[0]

    with log.name_and_fields('itunes', front=front, country=country):
        url = 'https://itunes.apple.com/app/id{0}?mt=8'.format(app_id)
        headers = {'X-Apple-Store-Front': '{0}-2,28'.format(front)}
        response = requests.get(url, headers=headers)
        if response.status_code == 400 or response.status_code == 403:
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


def download(source, **params):
    """Processes iOS app's changelog from urls like these
    https://itunes.apple.com/in/app/temple-run/id420009108?mt=8
    https://itunes.apple.com/en/app/slack-team-communication/id618783545?l=en&mt=8
    """
    with log.name_and_fields('appstore', source=source):
        log.info('Downloading')
        app_id = get_itunes_app_id(source)
        data = get_itunes_release_notes(app_id)
        if data:
            history = data['pageData']['softwarePageData']['versionHistory']
            if history:
                def format_item(item):
                    version = item['versionString']
                    date = item['releaseDate']
                    notes = item.get('releaseNotes') or 'No description'
                    notes = notes.replace(u'•', u'*') # because of vk.com mothefuckers
                    notes = notes.replace(u'★', u'*') # because of temple run motherfuckers
                    text = u"""
## {version} ({date})

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
