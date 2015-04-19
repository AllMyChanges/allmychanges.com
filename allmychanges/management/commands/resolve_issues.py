from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.models import Issue, User


class Command(LogMixin, BaseCommand):
    help = u"""Resolves issues of given type."""

    def handle(self, *args, **options):
        issue_type = args[0]
        issues = Issue.objects.filter(type=issue_type)
        by_user = User.objects.get(username='svetlyak40wt')

        for issue in issues:
            issue.resolve(by_user)
