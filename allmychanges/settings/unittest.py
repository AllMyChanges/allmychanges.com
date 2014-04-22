from .default import *  # nopep8

DATABASES['default'].update({
    'NAME': DATABASES['default']['NAME'] + '_unittest',
})

# this need for NoseDjango
DATABASE_NAME = DATABASES['default']['NAME']


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

LOG_FILENAME = 'unittest-' + CURRENT_USER + '.log'
init_logging(LOG_FILENAME)

# making jobs run synchronously without queueing
for queue_options in RQ_QUEUES.itervalues():
    queue_options['ASYNC'] = False

