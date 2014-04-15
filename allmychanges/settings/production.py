from .default import *  # nopep8

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
})


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 1,
        'PASSWORD': '',
    }
}

DATABASES['default'].update({
    'NAME': 'allmychanges',
})

GRAPHITE_PREFIX = 'allmychanges'

ALLOWED_HOSTS = ['allmychanges.com']

METRIKA_ID = '22434466'
ANALYTICS_ID = 'UA-49927178-1'

LOG_FILENAME = '/var/log/allmychanges/django-root.log'
init_logging(LOG_FILENAME)
