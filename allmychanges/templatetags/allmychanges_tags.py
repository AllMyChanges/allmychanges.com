import re
import anyjson

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from allmychanges.utils import reverse

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


@register.filter
def project_name(changelog):
    return u'{0.namespace}/{0.name}'.format(changelog)


@register.filter
def project_link(changelog):
    link = u'<a href="{0}">{1}</a>'.format(
        changelog.get_absolute_url(),
        project_name(changelog))
    return mark_safe(link)


@register.filter
def admin_user_links(users):
    """Outputs html fragment, with usernames linked to
    user profiles in admin interface."""
    def get_link(user):
        username = user.username
        return u'<a href="{0}">{1}</a>'.format(
            reverse('admin-user-profile',
                    username=username),
            username)
    fragment = u', '.join(map(get_link, users))
    return mark_safe(fragment)


@register.simple_tag
def avatars_list(users):
    size = 24

    def format_user(u):
        username = u.username
        return format_html(
            u'<a href="{profile_url}" title="{username}"><img width="{size}" src="{avatar_url}" /></a>',
            profile_url=reverse(
                'user-profile',
                username=username
            ),
            username=username,
            size=size,
            avatar_url=u.get_avatar(size),
        )
    users = map(format_user, users)
    return u', '.join(users)
