import os
from .default import *  # nopep8

ENVIRONMENT = 'production'
DEBUG = False
TEMPLATE_DEBUG = DEBUG

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
})


DATABASES['default'].update({
    'NAME': 'allmychanges',
})

GRAPHITE_PREFIX = 'allmychanges'

ALLOWED_HOSTS = ['allmychanges.com', 'localhost', 'new1.allmychanges.com']

METRIKA_ID = '22434466'
ANALYTICS_ID = 'UA-49927178-1'

SLACK_URLS = {
}

TWITTER_CREDS = ()

LOG_FILENAME = '/var/log/allmychanges/django.log'
try:
    init_logging(LOG_FILENAME, logstash=True)
except OSError:
    pass


if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

make_db_aliases()
