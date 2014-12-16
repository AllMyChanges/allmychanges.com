import re

from django.core import validators


class URLValidator(validators.URLValidator):
    """Custom url validator to include git urls
    """
    regex = re.compile(
        r'^(?:(?:http|ftp|)s?|git)://'  # http:// or https:// or git://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __call__(self, value):
        super(URLValidator, self).__call__(value)
