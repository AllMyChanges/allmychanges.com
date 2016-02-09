# coding: utf-8

import os
from .default import *  # nopep8

ENVIRONMENT = 'development'
DEBUG = os.environ.get('DEBUG', 'no') == 'yes'
TEMPLATE_DEBUG = DEBUG

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

METRIKA_ID = '24627125'
ANALYTICS_ID = 'UA-49927178-2'

# временно закомментировано, потому что на моем текущем окружении не работает
# скриншутилка, а надо было прогнать все авдейты на новом механизме даунлоадеров
#
# TWITTER_CREDS = ('KuAbS2vX9eM5fOrGJ2KPQm4gH',
#                  'kBkPXY0UuVmoCxHwY38SVkCL0dh5AJJdlNeJtrUgpQ9rBj6T1b',
#                  '3260479588-Fjoj5ATZHgepipegP2IxFTL675s2bVpfCzT3G3v',
#                  '6SeGn2urZzs2ztBuRLD4GdTVuejPx170uAoFEHMXgBfBl')


LOG_FILENAME = '/var/log/allmychanges/django-' + CURRENT_USER + '.log'
init_logging(LOG_FILENAME)


if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


ALLOWED_HOSTS = ['localhost',
                 'art.dev.allmychanges.com',
                 'skate.svetlyak.ru',
                 'dev.allmychanges.com']


SLACK_URLS = {}

make_db_aliases()
