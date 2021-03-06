from .default import *  # nopep8


ENVIRONMENT = 'unittest'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
DISABLE_TRANSACTION_MANAGEMENT = True

DATABASE_NAME = ''


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOG_FILENAME = '/var/log/allmychanges/unittest.log'

init_logging(LOG_FILENAME)

# making jobs run synchronously without queueing
for queue_options in RQ_QUEUES.itervalues():
    queue_options['ASYNC'] = False

#DEBUG = False
#TEMPLATE_DEBUG = False
DEBUG_JOBS = True

SLACK_URLS = None

make_db_aliases()
