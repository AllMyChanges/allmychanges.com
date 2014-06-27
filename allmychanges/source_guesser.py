import requests
import re

from .utils import normalize_url


def _get_data(data, path):
    def iterate(data, path):
        head = path[0]
        tail = path[1:]

        value = data.get(head)
        if value is None:
            return None
        else:
            if tail:
                return iterate(value, tail)
            else:
                return value
    return iterate(data, path.split('.'))


def _append_url(results, url):
    if url:
        url, _, _ = normalize_url(url, github_template='https://github.com/{username}/{repo}')
        if url not in results:
            results.append(url)


def _python_guesser(name):
    results = []
    response = requests.get('https://pypi.python.org/pypi/' + name)

    urls = re.findall(r'"(https?://.*?)"', response.content)
    for url in urls:
        if ('git' in url or 'bitbucket' in url) and \
           not ('issues' in url or 'gist' in url):
            _append_url(results, url)
    return results


def _perl_guesser(name):
    results = []
    hits = []
    
    # first, wee look for explicit match
    response = requests.get('http://api.metacpan.org/v0/release/' + name)
    if response.status_code == 200:
        hits.append(response.json())

    # next try to search because first match coculd be
    response = requests.get('http://api.metacpan.org/v0/release/_search?q=' + name.lower())
    
    if response.status_code == 200:
        data = response.json()
        hits.extend([_get_data(item, '_source.metadata')
                     for item in data['hits']['hits']])

    for hit in hits:
        _append_url(results, _get_data(hit, 'resources.repository.url'))
        _append_url(results, _get_data(hit, 'resources.homepage'))

    return results


def guess_source(namespace, name):
    guesser = globals().get('_{0}_guesser'.format(namespace))
    if guesser:
        return guesser(name)
    return []
