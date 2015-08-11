import re


def normalize_url(url, for_checkout=True, return_itunes_data=False):
    """Normalize url either for browser or for checkout.
    Usually, difference is in the schema.
    It normalizes url to 'git@github.com:{username}/{repo}' and also
    returns username and repository's name.
    """
    for_browser = not for_checkout
    github_template = 'git://github.com/{username}/{repo}'
    bitbucket_template = 'https://bitbucket.org/{username}/{repo}'

    if for_browser:
        github_template = 'https://github.com/{username}/{repo}'

    url = url.replace('git+', '')

    if 'github' in url:
        regex = r'github.com[/:](?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]+?)(?:\.git$|/$|/tree/master$|$)'
        match = re.search(regex, url)
        if match is None:
            # some url to a raw file or github wiki
            return (url, None, None)
        else:
            username, repo = match.groups()
            return (github_template.format(**locals()),
                    username,
                    repo)


    elif 'bitbucket' in url:
        regex = r'bitbucket.org/(?P<username>[A-Za-z0-9-_]+)/(?P<repo>[^/]*)'
        username, repo = re.search(regex, url).groups()
        return (bitbucket_template.format(**locals()),
                username,
                repo)
    elif 'itunes.apple.com' in url:
        app_id = get_itunes_app_id(url)
        data = get_itunes_app_data(app_id)
        if data:
            # here we add iTunes Affilate token
            result = [data['trackViewUrl'] + '&at=1l3vwNn', None, None]
            if return_itunes_data:
                result.append(data)
            return result

    return (url, None, url.rsplit('/')[-1])
