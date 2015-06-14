import re
from django.conf import settings

UNRELEASED_RE = re.compile(ur'|'.join(settings.UNRELEASED_KEYWORDS), flags=re.I)


def mention_unreleased(text):
    return UNRELEASED_RE.search(text) is not None
