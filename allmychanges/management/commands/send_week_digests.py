from allmychanges.management.commands.send_digests import Command as BaseCommand


class Command(BaseCommand):
    period = 'week'
