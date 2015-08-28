import tempfile
import os
import shutil

from django.conf import settings


def guess(source, discovered):
    if source.startswith('test+'):
        return {'source': source}


def download(source,
             search_list=[],
             ignore_list=[]):
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
