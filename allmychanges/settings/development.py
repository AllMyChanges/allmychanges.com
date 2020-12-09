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

LOG_FILENAME = '/var/log/allmychanges/django.log'
init_logging(LOG_FILENAME)


if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


ALLOWED_HOSTS = ['localhost',
                 'art.dev.allmychanges.com',
                 'skate.svetlyak.ru',
                 'dev.allmychanges.com',
                 'allmychanges.localhost',
                ]

BASE_URL = 'http://dev.allmychanges.com'


SLACK_URLS = {}

make_db_aliases()
