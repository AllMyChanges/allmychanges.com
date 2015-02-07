from distutils.version import StrictVersion, LooseVersion


def compare_versions(version1, version2):
    try:
        value = cmp(StrictVersion(version1), StrictVersion(version2))
        return value
    # in case of abnormal version number, fall back to LooseVersion
    except ValueError:
        pass

    try:
        value = cmp(LooseVersion(version1), LooseVersion(version2))
        return value
    except TypeError:
    # certain LooseVersion comparions raise due to unorderable types,
    # fallback to string comparison
        value = cmp([str(v) for v in LooseVersion(version1).version],
                    [str(v) for v in LooseVersion(version2).version])
        return value


def reorder_versions(version_objects):
    version_objects.sort(cmp=lambda left, right: compare_versions(
        left.number, right.number))

    for idx, obj in enumerate(version_objects):
        obj.order_idx = idx
        obj.save(update_fields=('order_idx',))

    return version_objects
