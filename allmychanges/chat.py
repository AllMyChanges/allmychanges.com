import anyjson
import requests

from django.conf import settings

# these messages filled instead of sending
# during unittests
messages = []

def send(text):
    if settings.SLACK_URL:
        requests.post(settings.SLACK_URL, data=anyjson.serialize(dict(text=text)))
    else:
        messages.append(text)


def clear_messages():
    messages[:] = []
