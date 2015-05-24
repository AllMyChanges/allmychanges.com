from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges import crm
from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Sync all users data with our CRM system."""

    def handle(self, *args, **options):
        for user in User.objects.all():
            crm.sync(user)
