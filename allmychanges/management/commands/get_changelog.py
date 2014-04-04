import os

from django.core.management.base import BaseCommand

from allmychanges.crawler import search_changelog, _parse_changelog_text
from allmychanges.models import Repo
from allmychanges.utils import cd, get_package_metadata, download_repo


class Command(BaseCommand):
    help = u"""Updates single project."""

    def handle(self, *args, **options):
        for path in args:
            self._update(path)

    def _update(self, url):
        if '://' in url or url.startswith('git@'):
            path = download_repo(url)
        else:
            path = url

        with cd(path):
            changelog_filename = search_changelog()
            if changelog_filename:
                fullfilename = os.path.normpath(
                    os.path.join(os.getcwd(), changelog_filename))

                with open(fullfilename) as f:
                    changes = _parse_changelog_text(f.read())

                    if changes:
                        repo, created = Repo.objects.get_or_create(
                            url=url,
                            title=get_package_metadata('.', 'Name'))
                        repo.versions.all().delete()

                        for change in changes:
                            version = repo.versions.create(
                                name=change['version'])

                            for section in change['sections']:
                                item = version.items.create(
                                    text=section['notes'])

                                for section_item in section['items']:
                                    item.changes.create(type='new',
                                                        text=section_item)
