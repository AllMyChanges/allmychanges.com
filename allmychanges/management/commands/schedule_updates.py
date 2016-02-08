from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.tasks import schedule_updates
from allmychanges.models import Version


class Command(LogMixin, BaseCommand):
    help = u"""Updates single project."""

    def handle(self, *args, **options):
        special_keywords = ['reschedule', 'full']
        reschedule = True if args and 'reschedule' in args else False
        full = True if args and 'full' in args else False
        packages = [name
                    for name in args
                    if name not in special_keywords]

        if full:
            if packages:
                Version.objects.filter(changelog__name__in=packages).delete()
            else:
                Version.objects.all().delete()

        schedule_updates.delay(reschedule=reschedule,
                               packages=packages)
