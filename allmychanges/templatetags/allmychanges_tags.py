import re
import anyjson

from django import template


register = template.Library()


@register.filter
def json(value):
    return anyjson.serialize(value)


@register.filter
def order_by(value, arg):
    return value.order_by(arg)


@register.filter
def remove_source_prefix(value):
    return value.split('+', 1)[-1]


@register.filter
def process_cve(value):
    return re.sub(r'(CVE-\d+-\d+)',
                  r'<a href="http://cve.mitre.org/cgi-bin/cvename.cgi?name=\1">\1</a>',
                  value)

@register.filter
def replace_dots(value):
    return value.replace('.', '-')

@register.filter
def debug(value):
    import pdb; pdb.set_trace()  # DEBUG
    return value

@register.filter
def screenshot_url(request):
    return request.build_absolute_uri(request.path) + 'snap/'

@register.filter
def site_url(request):
    """Returns full site's url without a backslash at the end.
    """
    if isinstance(request, basestring):
        # probably called from email sender
        return 'https://allmychanges.com'
    return request.build_absolute_uri('/').rstrip('/')
