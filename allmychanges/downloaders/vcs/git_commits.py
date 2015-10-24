import tempfile
import envoy
import os


from collections import defaultdict
from django.conf import settings
from allmychanges.downloaders.vcs.git import download as git_download
from allmychanges.vcs_extractor import get_versions_from_vcs
from allmychanges.env import Environment, serialize_envs


def download(source,
             search_list=[],
             ignore_list=[]):
    print 'DOWNLOAD'
    if True:
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



def guess(source, discovered={}):
    print 'GUESS'
    result = defaultdict(dict)
    result['changelog']['source'] = source
    return result
