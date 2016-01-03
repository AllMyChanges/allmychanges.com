import re
import os
import tempfile
import shutil

from collections import defaultdict
from django.conf import settings
from allmychanges.utils import (
    log,
    first_sentences)


def guess(source, discovered={}):
    from allmychanges.models import DESCRIPTION_LENGTH

    with log.name_and_fields('google_play', source=source):
        log.info('Guessing')

        if not 'play.google.com' in source:
            return

        result = defaultdict(dict)

        try:
            app_id = google_play_get_id(source)
            api = google_play_get_api()
            response = api.details(app_id)

            name = response.docV2.title
            if name:
                name = name.split(' -', 1)[0]

            description = response.docV2.descriptionHtml
            if description:
                description = first_sentences(description,
                                              DESCRIPTION_LENGTH)

            images = response.docV2.image
            if images:
                icon = images[0].imageUrl
            else:
                icon = None

            # if everything is OK, start populating result
            result['changelog']['source'] = source
            result['stop'] = True

            result['changelog'].update(dict(
                namespace='android',
                name=name,
                description=description,
                icon=icon))
        except Exception:
            # TODO: remove or not
            raise
            pass

        return result

def google_play_get_id(source):
    match = re.search(ur'id=(?P<app_id>[^&]+)', source)
    if match is None:
        raise RuntimeError('Unable to extract app id from source URL')
    return match.group('app_id')


def google_play_get_api():
    from googleplayapi.googleplay import GooglePlayAPI
    api = GooglePlayAPI(settings.GOOGLE_PLAY_DEVICE_ID)
    api.login(settings.GOOGLE_PLAY_USERNAME,
              settings.GOOGLE_PLAY_PASSWORD)
    return api


def download(source, **params):
    """Downloads latest release note from Google Play.
    """
    with log.name_and_fields('google_play', source=source):
        log.info('Downloading')

        app_id = google_play_get_id(source)
        api = google_play_get_api()
        response = api.details(app_id)

        version = response.docV2.details.appDetails.versionString
        changes = response.docV2.details.appDetails.recentChangesHtml
        release_date = response.docV2.details.appDetails.uploadDate

        content = u"""
    {version} ({date})
    ====================

    {changes}
    """.format(version=version,
               date=release_date,
               changes=changes)

        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
        inner_path = os.path.join(path, 'GooglePlay')
        os.mkdir(inner_path)
        try:
            with open(os.path.join(inner_path, 'ChangeLog'), 'w') as f:
                f.write(content.encode('utf-8'))

        except Exception, e:
            if os.path.exists(path):
                shutil.rmtree(path)
            raise RuntimeError('Unexpected exception "{0}" when fetching google app: {1}'.format(
                repr(e), source))
        return path
