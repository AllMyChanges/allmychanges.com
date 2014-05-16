# coding: utf-8
import string

from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin

from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Imports packages into user digest, first argument is username, second — filename."""

    def handle(self, *args, **options):
        username, filename = args
        user = User.objects.get(username=username)
        with open(filename) as f:
            packages = f.readlines()
            packages = (p.split(';') for p in packages)
            packages = (map(string.strip, p) for p in packages)

            added = 0
            already_exists = 0

            for namespace, name, source in packages:
                if user.packages.filter(namespace=namespace,
                                        name=name).count() > 0:
                    already_exists += 1
                else:
                    user.packages.create(namespace=namespace,
                                         name=name,
                                         source=source)
                    added += 1

            if added:
                print added, 'packages were added'
                
            if already_exists:
                print already_exists, 'packages already present'
