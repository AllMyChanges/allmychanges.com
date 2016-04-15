import mock

from allmychanges.tasks import update_changelog_task
from allmychanges.models import Changelog
from .utils import refresh, eq_, dt_eq
from django.utils import timezone


def test_update_changelog_task_stops_future_changelog_updates_in_case_of_error():
    changelog = Changelog.objects.create(
        namespace='python', name='pip', source='test')

    with mock.patch('allmychanges.tasks.update_preview_or_changelog') as func:
        func.side_effect = RuntimeError('Blah minor')
        update_changelog_task(changelog.id)

    changelog = refresh(changelog)
    dt_eq(changelog.paused_at, timezone.now())

    eq_(1, changelog.issues.count())

    issue = changelog.issues.all()[0]
    eq_('auto-paused', issue.type)
    eq_('Paused because of error: "Blah minor"', issue.comment)
