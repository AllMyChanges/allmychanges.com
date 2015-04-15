from ..models import Changelog

def add_default_package(strategy, is_new=None, user=None, *args, **kwargs):
    if is_new:
        try:
            changelog = Changelog.objects.get(
                namespace='web', name='allmychanges')
        except Changelog.DoesNotExist:
            changelog = Changelog.objects.create(
                namespace='web', name='allmychanges',
                source='https://allmychanges.com/CHANGELOG.md')

        user.track(changelog)
