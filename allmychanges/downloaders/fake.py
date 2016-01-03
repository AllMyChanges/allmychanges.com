import tempfile
import os
import shutil

from django.conf import settings
from allmychanges.utils import log


def guess(source, discovered):
    with log.name_and_fields('fake', source=source):
        log.info('Guessing')
        if source.startswith('test+'):
            return {'source': source}


def download(source, **params):
    with log.name_and_fields('fake', source=source):
        log.info('Downloading')

        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)

        source = source.replace('test+', '')

        if os.path.isfile(source):
            shutil.copyfile(
                source,
                os.path.join(path, 'CHANGELOG'))
            return path
        else:
            destination = os.path.join(path, 'project')
            shutil.copytree(source, destination)
            return destination
