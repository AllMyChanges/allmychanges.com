from allmychanges.models import Changelog, User


def _parse_name(name):
    """Returns a pair namespace, name
    parsing string like namespace/name.

    Namespace could be None if there is not backslash in the name.
    """
    if '/' in name:
        return name.split('/', 1)
    return None, name

def _nonnull_dict(**kwargs):
    """Returns a dict containing all kwargs except thouse having a None value.
    """
    return {key: value
            for key, value in kwargs.items()
            if value is not None}


def ch(name):
    """Returns a changelog with given name
    """
    namespace, name = _parse_name(name)
    params = _nonnull_dict(namespace=namespace,
                          name=name)
    return Changelog.objects.get(**params)


def u(name):
    """Returns user with given name"""
    return User.objects.get(username=name)
