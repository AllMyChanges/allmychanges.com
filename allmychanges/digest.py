from collections import defaultdict
from allmychanges.models import Changelog, FeedItem
from allmychanges.views import get_package_data_for_template
from django.utils import timezone


def get_digest_for(user):
    # fetch versions
    versions = user.feed_versions.filter(feed_items__id__gt=user.feed_sent_id)

    # group them by changelog
    changelog_id_to_versions = defaultdict(list)
    for version in versions:
        changelog_id_to_versions[version.changelog_id].append(version)

    # fetch changelogs
    changelog_ids = changelog_id_to_versions.keys()
    changelogs = Changelog.objects.filter(pk__in=changelog_ids)

    changes = [
        get_package_data_for_template(
            changelog,
            versions=changelog_id_to_versions[changelog.id])
        for changelog in changelogs]

    return changes


def mark_digest_sent_for(user):
    latest_item = FeedItem.objects.filter(user=user).latest('id')
    user.feed_sent_id = latest_item.id
    user.last_digest_sent_at = timezone.now()
    user.save(update_fields=(
        'feed_sent_id',
        'last_digest_sent_at'))
