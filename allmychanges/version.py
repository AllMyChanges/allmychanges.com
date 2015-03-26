from itertools import takewhile
from types import IntType, LongType
from distutils.version import (
    StrictVersion,
    StringType,
    LooseVersion as BaseLooseVersion)


num_types = (IntType, LongType)
is_number = lambda value: isinstance(value, num_types)


def separate_numbers(sequence):
    iterator = iter(sequence)
    numbers = tuple(takewhile(is_number, iterator))
    remainder = tuple(iterator)
    return numbers, remainder


class LooseVersion(BaseLooseVersion):
    def __cmp__ (self, other):
        if isinstance(other, StringType):
            other = LooseVersion(other)

        self_numbers, self_remainder = separate_numbers(self.version)
        other_numbers, other_remainder = separate_numbers(other.version)

        numbers_cmp = cmp(self_numbers, other_numbers)
        if numbers_cmp != 0:
            return numbers_cmp

        # empty suffix means greater version
        # for example: 0.8.2 > 0.8.2-beta
        if not self_remainder:
            return 1
        if not other_remainder:
            return -1

        # if both remainders not empty
        # 0.8.2-alpha < 0.8.2-beta
        remainders_cmp = cmp(self_remainder, other_remainder)
        return remainders_cmp


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
