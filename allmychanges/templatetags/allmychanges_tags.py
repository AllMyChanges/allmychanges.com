import anyjson
from django import template

register = template.Library()


@register.filter
def json(value):
    return anyjson.serialize(value)
