import os
import MySQLdb.cursors


here = lambda * x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

PROJECT_ROOT = here('..', '..')
root = lambda * x: os.path.join(os.path.abspath(PROJECT_ROOT), *x)

CURRENT_USER = os.environ.get('USER', os.environ.get('LOGNAME', 'root'))

DEBUG = False
TEMPLATE_DEBUG = DEBUG
DEBUG_JOBS = False

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
#        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

def make_db_aliases():
    # To keep one connection for reading from server-side corsor
    # and to write to the second
    if not os.environ.get('MIGRATIONS'):
        DATABASES['server-side'] = DATABASES['default'].copy()
        DATABASES['server-side']['OPTIONS'] = {
#            'charset': 'utf8mb4',
            'cursorclass': MySQLdb.cursors.SSCursor}

        # for parallel transactions
        DATABASES['parallel'] = DATABASES['default'].copy()


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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

BASE_URL = 'http://skate.svetlyak.ru'

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
SNAPSHOTS_ROOT = os.path.join(STATIC_ROOT, 'shots')


# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'
SNAPSHOTS_URL = '/static/shots/'

# Additional locations of static files
# STATICFILES_DIRS = (
# )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
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
    'allmychanges.middleware.LightUserMiddleware',
    'twiggy_goodies.django.LogMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
    'django.contrib.sitemaps',

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
    'compressor',
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

REDIS_HOST = os.environ.get('REDIS.ALLMYCHANGES.COM_PORT_6379_TCP_ADDR', 'local')
REDIS_PORT = int(os.environ.get('REDIS.ALLMYCHANGES.COM_PORT_6379_TCP_PORT', 6379))

RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0,
        'PASSWORD': '',
    },
    'preview': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0,
        'PASSWORD': '',
    }
}

GRAPHITE_PREFIX = 'allmychanges.' + CURRENT_USER
GRAPHITE_HOST = 'salmon.svetlyak.ru'


TEMP_DIR = '/tmp/allmychanges'

EMAIL_BACKEND = 'django_sendmail_backend.backends.EmailBackend'

# how to get a token:
# http --auth svetlyak40wt https://api.github.com/authorizations scopes:='["public_repo"]' note="Background allmychanges process." client_id="f1106b299e606f5ae13c" client_secret="xxx"
# copy client_secret from https://github.com/settings/applications/91994
GITHUB_TOKEN = '6d7d8605f0d53f29b6e049267e8bcbc80577b27f'
SLACK_URLS = {
    'default': 'https://hooks.slack.com/services/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'
}
CLOSEIO_KEY = '34c5992096c7f67bd5d22f24e4e87a5837f58af5f326f2cdfda932d4'
MANDRILL_KEY = 'g3pUEIJTBEd6KGeWkKihgQ'
# AllMyChangesBot
TELEGRAM_BOT_BASE_URL = 'https://api.telegram.org/bot99002009:AAF2epqrBGImWKPANN1GWTnUsI0fxIUpTI0/'


# these are used to post tweets about new versions
TWITTER_CREDS = None

UNRELEASED_KEYWORDS = set([
    'unreleased',
    'under development',
    'not released yet',
    'not yet released',
    'release date.*to be decided',
    'release date.*to be determined',
    'in-progress',
])

HTTP_USER_AGENT = 'AllMyChanges.com Bot'

GOOGLE_PLAY_DEVICE_ID = '392B42751B25945B'
GOOGLE_PLAY_USERNAME = None
GOOGLE_PLAY_PASSWORD = None

# people who can edit and sed templates
ADVANCED_EDITORS = set(['svetlyak40wt', 'Bugagazavr'])

from .auth import *  # nopep8
from secure_settings import *  # nopep8


def init_logging(filename, logstash=False):
    import logging
    from twiggy import add_emitters, outputs, levels, formats
    from twiggy_goodies.std_logging import RedirectLoggingHandler
    from twiggy_goodies.json import JsonOutput
    from twiggy_goodies.logstash import LogstashOutput


    def is_stats(msg):
        return msg.name.startswith('stats')

    add_emitters(('all',
                 levels.DEBUG,
                 lambda msg: not is_stats(msg),
                 JsonOutput(filename.format(user=CURRENT_USER))))

    if logstash:
        add_emitters(('all-to-logstash',
                     levels.DEBUG,
                     lambda msg: not is_stats(msg),
                     LogstashOutput('salmon.svetlyak.ru', 6543)))

    add_emitters(('stats',
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


# http://lxml.de/1.3/extensions.html
import re
from lxml import etree
ns = etree.FunctionNamespace('http://allmychanges.com/functions')
ns.prefix = 'amch'

def sub(context, pattern, replacement, text):
    if isinstance(text, (list, tuple)):
        text = text[0]
    return re.sub(pattern, replacement, text)
ns['re.sub'] = sub

def match(context, pattern, text):
    if isinstance(text, (list, tuple)):
        text = text[0]
    return re.match(pattern, text) is not None
ns['re.sub'] = sub


SHELL_PLUS_PRE_IMPORTS = (
    ('allmychanges.shell', '*'),
)
