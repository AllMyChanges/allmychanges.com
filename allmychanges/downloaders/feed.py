import os
import feedparser
import shutil
import tempfile

from django.conf import settings
from collections import defaultdict
from allmychanges.downloaders.utils import feedfinder
from twiggy_goodies.threading import log

def guess(source, discovered={}):
    with log.name_and_fields('feed', source=source):
        log.info('Guessing')
        result = defaultdict(dict)

        try:
            feeds = feedfinder.feeds(source)

            if feeds:
                # if everything is OK, start populating result
                result['changelog']['source'] = feeds[0]
        except Exception:
            pass

        return result


def download(source, **params):
    with log.name_and_fields('feed', source=source):
        log.info('Downloading')

        source = source.replace('rss+', '').replace('atom+', '').replace('feed+', '')
        feed = feedparser.parse(source)
        path = tempfile.mkdtemp(dir=settings.TEMP_DIR)

        try:
            with open(os.path.join(path, 'feed.html'), 'w') as f:
                f.write('<html><body>\n\n')

                for entry in feed['entries']:
                    f.write((u'<h1>{title}</h1>\n'
                             '<div style="display: none">'
                             '{published}</div>\n\n{summary}\n\n').format(
                                 title=entry.title,
                                 published=getattr(entry, 'published', entry.updated),
                                 summary=entry.summary).encode('utf-8'))
                f.write('</body></html>')
        except Exception:
            if os.path.exists(path):
                shutil.rmtree(path)
            raise
        return path
