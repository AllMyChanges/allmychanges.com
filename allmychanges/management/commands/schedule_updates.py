from django.core.management.base import BaseCommand

from allmychanges.tasks import schedule_updates

class Command(BaseCommand):
    help = u"""Updates single project."""

    def handle(self, *args, **options):
        reschedule = True if args and args[0] == 'reschedule' else False
        schedule_updates.delay(reschedule=reschedule)
