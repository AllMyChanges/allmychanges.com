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
