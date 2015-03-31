import os
from .default import *  # nopep8

DEBUG = os.environ.get('DEBUG', 'no') == 'yes'
TEMPLATE_DEBUG = DEBUG

if DEBUG:
    INSTALLED_APPS += (
        'debug_toolbar',
    )

    # debug toolbar settings
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': 'allmychanges.utils.show_debug_toolbar'
    }


METRIKA_ID = '24627125'
ANALYTICS_ID = 'UA-49927178-2'


LOG_FILENAME = '/var/log/allmychanges/django-' + CURRENT_USER + '.log'
init_logging(LOG_FILENAME)


if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


ALLOWED_HOSTS = ['localhost', 'art.dev.allmychanges.com']
