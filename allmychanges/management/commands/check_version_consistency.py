from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Changelog


def parse_version(text):
    try:
        return tuple(map(int, text.split('.')))
    except:
        return ()


def check_versions(versions):
    if versions:
        previous = versions[0]
        for version in versions[1:]:
            if version < previous:
                return (previous, version)
            previous = version
    return None


def check_changelog(changelog):
    versions = changelog.versions.all().order_by('id')
    numbers = [parse_version(v.number) for v  in versions]
    return check_versions(numbers)


class Command(LogMixin, BaseCommand):
    help = u"""Tests crawler on selected projects."""

    def handle(self, *args, **options):
        changelogs = Changelog.objects.all()
        num_problems = 0

        for changelog in changelogs:
            result = check_changelog(changelog)
            if result:
                num_problems += 1
                prev_version, version = result
                print changelog.namespace, changelog.name, '{0} > {1}'.format(
                    '.'.join(map(str, prev_version)),
                    '.'.join(map(str, version)))

        print 'Num problems:', num_problems
