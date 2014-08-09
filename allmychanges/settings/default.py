import os
here = lambda * x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

PROJECT_ROOT = here('..', '..')
root = lambda * x: os.path.join(os.path.abspath(PROJECT_ROOT), *x)

CURRENT_USER = os.environ.get('USER', os.environ.get('LOGNAME', 'root'))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'allmychanges_' + CURRENT_USER.replace('-', '_'),
        'USER': 'allmychanges',
        'PASSWORD': 'allmychanges',
        'HOST': '',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = root('static')


# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
# STATICFILES_DIRS = (
# )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
# SECRET_KEY = 'Bad Idea'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'allmychanges.middleware.TurnOffCSRFProtectionIfOAuthenticated',
    'twiggy_goodies.django.LogMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

#X_FRAME_OPTIONS = 'ALLOW-FROM metrika.yandex.ru'

ROOT_URLCONF = 'allmychanges.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'allmychanges.wsgi.application'

TEMPLATE_DIRS = (
    root('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'south',
    'rest_framework',
    'django_rq',
    'django_extensions',

    'allmychanges',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    'social.apps.django_app.default',
    'django_markdown2',
    'widget_tweaks',
    'oauth2_provider',
)

AUTH_USER_MODEL = 'allmychanges.User'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# all logging goes through twiggy
LOGGING_CONFIG = False

# rest framework
REST_FRAMEWORK = {
    'PAGINATE_BY': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    )
}


REPO_ROOT = root('data')


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': '',
    }
}

GRAPHITE_PREFIX = 'allmychanges.' + CURRENT_USER
GRAPHITE_HOST = 'salmon.svetlyak.ru'


TEMP_DIR = '/tmp/allmychanges'

EMAIL_BACKEND = 'django_sendmail_backend.backends.EmailBackend'

from .auth import *  # nopep8
from secure_settings import *  # nopep8

def init_logging(filename, logstash=False):
    import logging
    from twiggy import addEmitters, outputs, levels, formats
    from twiggy_goodies.std_logging import RedirectLoggingHandler
    from twiggy_goodies.json import JsonOutput
    from twiggy_goodies.logstash import LogstashOutput


    def is_stats(msg):
        return msg.name.startswith('stats')

    addEmitters(('all',
                 levels.DEBUG,
                 lambda msg: not is_stats(msg),
                 JsonOutput(filename.format(user=CURRENT_USER))))

    if logstash:
        addEmitters(('all-to-logstash',
                     levels.DEBUG,
                     lambda msg: not is_stats(msg),
                     LogstashOutput('salmon.svetlyak.ru', 6543)))

    addEmitters(('stats',
                 levels.DEBUG,
                 is_stats,
                 outputs.FileOutput(filename.format(user=CURRENT_USER).replace('django-', 'stats-'),
                                    format=formats.line_format)))

    handler = RedirectLoggingHandler()
    del logging.root.handlers[:]
    logging.root.addHandler(handler)

    # we need this, to turn off django-rq's logging
    # configuration
    worker_logger = logging.getLogger('rq.worker')
    del worker_logger.handlers[:]
    worker_logger.addHandler(handler)
    worker_logger.propagate = False

    # and we need this to turn off python-rq's logging
    # configuration
    logging._handlers['fake-handler'] = handler
