import requests
import os

from collections import defaultdict
from allmychanges.downloaders.utils import feedfinder


def guess(source, discovered={}):
    result = defaultdict(dict)

    try:
        feeds = feedfinder.feeds(source)

        if feeds:
            # if everything is OK, start populating result
            result['changelog']['source'] = feeds[0]
    except:
        raise
        pass

    return result


def download(source,
             search_list=[],
             ignore_list=[]):
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
    except:
        if os.path.exists(path):
            shutil.rmtree(path)
        raise
    return path
