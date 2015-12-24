import tempfile
import envoy
import os


from django.conf import settings
from twiggy_goodies.threading import log
from allmychanges.downloaders.vcs.git import (
    download as git_download,
    guess as git_guess)
from allmychanges.vcs_extractor import (
    get_versions_from_vcs,
    choose_version_extractor)
from allmychanges.crawler import _extract_version
from allmychanges.env import Environment, serialize_envs
from allmychanges.utils import cd


def guess(*args, **kwargs):
    """We build changelog from commit messages only if there are
    tags like version numbers or a special version extractor is
    available for this repository.
    """

    def callback(path, result):
        with cd(path):
            log.info('Checking if there are suitable tags')
            response = envoy.run('git tag')
            tags = response.std_out.split('\n')
            tags = map(_extract_version, tags)
            tags = list(filter(None, tags))
            if tags:
                return result

            log.info('Checking if some version extractor is available')
            version_extractor = choose_version_extractor(path)
            if version_extractor is not None:
                return result

    return git_guess(callback=callback, *args, **kwargs)


def download(source, **params):
    if False:
        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)
        # import time
        # time.sleep(0)
        envoy.run('cp -r /app/fake/haproxy ' + path)
        path += '/haproxy'
    else:
        path = git_download(source)

    if path:
        env = Environment(dirname=path)
        versions = get_versions_from_vcs(env)

        with open(os.path.join(path, 'versions.amchenvs'), 'w') as f:
            f.write(serialize_envs(versions))

    return path
