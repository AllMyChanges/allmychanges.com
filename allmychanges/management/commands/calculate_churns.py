from django.core.management.base import BaseCommand
from twiggy_goodies.django import LogMixin
from allmychanges.churn import (
    get_user_actions_heatmap,
    calculate_churns,
    fill_churn_sequence)
from allmychanges.models import User


class Command(LogMixin, BaseCommand):
    help = u"""Calculate user churns and resurrections for graph."""

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            history = sorted(get_user_actions_heatmap(user).keys())
            churns = calculate_churns(history)
            state_history = fill_churn_sequence(churns)

            user.state_history.all().delete()
            for date, state in state_history:
                user.state_history.create(date=date, state=state)
