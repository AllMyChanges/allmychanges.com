def add_default_package(strategy, is_new=None, user=None, *args, **kwargs):
    if is_new:
        user.packages.create(namespace='web', name='allmychanges',
                             source='http+http://allmychanges.com/CHANGELOG.md')
