from allmychanges.management.commands.send_digests2 import Command as BaseCommand


class Command(BaseCommand):
    period = 'week'
