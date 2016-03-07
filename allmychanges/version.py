from itertools import takewhile, groupby
from types import IntType, LongType
from distutils.version import (
    StrictVersion,
    StringType,
    LooseVersion as BaseLooseVersion)


num_types = (IntType, LongType)
is_number = lambda value: isinstance(value, num_types)

def last(lst):
    if lst:
        return lst[-1]


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


def find_branches(versions):
    """Searches latest patch versions for all minor releases.
    Also, returns the latest version because it is a tip of the tree.
    If there isn't patch versions for some release, then it is not returned."""

    versions = map(LooseVersion, versions)

    # group versions by (major, minor) parts
    major_minor = lambda item: item.version[:2]
    versions.sort()
    tip = last(versions)
    grouped = groupby(versions, key=major_minor)

    chunks = (tuple(value) for key, value in grouped)

    # we only take versions which has patches
    chunks = (versions for versions in chunks if len(versions) > 1)

    # and we only need latest patch releases
    result = map(last, chunks)

    # we also add the last version bacause it is a tip
    if last(result) is not tip:
        result.append(tip)

    return [item.vstring for item in result]


def version_update_has_wrong_order(versions, new_versions):
    """Checks if new versions are out of order or there
    is something suspicious.
    If new_versions growth like:
    0.1.1, 0.1.2, 0.2.0
    it is ok.

    Or if it is update to existing branches, like
    when we have 0.2.0 and 0.3.4 versions of the library
    and suddenly 0.2.1 and 0.3.5 patch releases are out.

    Arguments versions and new_versions should be ordered.
    """
    branches = find_branches(versions)
    if not branches:
        return False

    tip = branches[-1]

    def find_branch_for_version(v):
        for branch in branches:
            if on_same_branch(branch, v):
                return branch
        return tip

    chunks = groupby(new_versions, find_branch_for_version)
    chunks = [[key] + list(values)
              for key, values
              in chunks]

    some_chunk_has_hole = any(map(has_hole, chunks))
    return some_chunk_has_hole


def follows(left, right):
    """Checks if right version can follow right after the left version.

    Should return True for (0.1.0 and 0.1.1)
    but False for (0.1.0 and 0.1.2)
    """
    left = LooseVersion(left)
    right = LooseVersion(right)
    some_part_was_incremented = False

    for left_item, right_item in zip(
            left.version,
            right.version):

        # for versions like 0.1.2-rc3 there will be
        # such parts: (0, 1, 2, '-', 'rc', 3)
        # and here we want to ignore parts which are
        # the same in left and right version
        if isinstance(left_item, basestring) \
           or isinstance(right_item, basestring):
            if left_item == right_item:
                continue
            else:
                return False

        difference = right_item - left_item

        if some_part_was_incremented and right_item != 0:
            # if there was higher part's increment, then right part
            # should be equal to zero
            return False

        if difference > 1:
            # if difference is too much
            return False
        elif difference < 0:
            # left part is bigger than right
            # then probably there was higher part's increment
            # if not, then this is a wrong order
            if not some_part_was_incremented:
                return False
        elif difference == 1:
            some_part_was_incremented = True
    return True


def on_same_branch(left, right):
    """Checks if left and right versions have difference only in the patch version

    Should return True for (0.1.0 and 0.1.1)
    but False for (0.1.0 and 0.2.0)
    """
    left = LooseVersion(left)
    right = LooseVersion(right)
    return left.version[:2] == right.version[:2]


def has_hole(versions):
    """Checks if each version in the list follows the previous one.
    """
    if len(versions) < 2:
        return False

    def compare(left, right):
        """If right version follows the left, then
        return right. Otherwise, return left.
        """
        if left is not None:
            if follows(left, right):
                return right

    result = reduce(compare, versions)
    return result is None
