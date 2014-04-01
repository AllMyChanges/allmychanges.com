from .default import *  # nopep8

DATABASES['default'].update({
    'NAME': DATABASES['default']['NAME'] + '_unittest',
})

# this need for NoseDjango
DATABASE_NAME = DATABASES['default']['NAME']


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)
