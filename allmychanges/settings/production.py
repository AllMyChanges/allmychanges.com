import os
from .default import *  # nopep8


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

BASE_URL = 'https://allmychanges.com'

GRAPHITE_PREFIX = 'allmychanges'

ALLOWED_HOSTS = ['allmychanges.com', 'localhost']

METRIKA_ID = '22434466'
ANALYTICS_ID = 'UA-49927178-1'
PINGDOM_ID = '55b0e587abe53dba777b23c6'

SLACK_URLS = {
    'default': 'https://hooks.slack.com/services/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',
    'tasks': 'https://hooks.slack.com/services/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',
}

TWITTER_CREDS = ('WjfgjgXOwgj2vjUrDYvebI91x',
                 'iyIGDiLzfFGDr0Kg0yF5x4gAt4zzgi3IjHEpTvoxs6pSeRSgSn',
                 '3260477051-94dnqE4lm3rx3PLqPhEbjR8SipmRMgcf8s5Pshd',
                 'di7AAGhtFT2PuCgztxqC3hLP6QcDIIHq2e9flRpUemVSw')

LOG_FILENAME = '/var/log/allmychanges/django-root.log'
try:
    init_logging(LOG_FILENAME, logstash=True)
except OSError:
    pass


if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

make_db_aliases()
