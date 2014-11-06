from ..models import Changelog

def add_default_package(strategy, is_new=None, user=None, *args, **kwargs):
    if is_new:
        changelog, created = Changelog.objects.get_or_create(
            namespace='web', name='allmychanges',
            source='http://allmychanges.com/CHANGELOG.md')
        user.track(changelog)
