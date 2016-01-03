import re
import anyjson
import requests
import threading

from django.conf import settings

# these messages filled instead of sending
# during unittests
messages = []
_threads = []
_threads_lock = threading.Lock()

def send(text, channel=None):
    # may be refactor it using notifications some day
    def remote_send():
        if settings.SLACK_URLS:
            requests.post(settings.SLACK_URLS.get(channel,
                                                  settings.SLACK_URLS['default']),
                          data=anyjson.serialize(dict(text=text)))

    thread = threading.Thread(target=remote_send)
    thread.start()
    with _threads_lock:
        _threads.append(thread)

    if not settings.SLACK_URLS:
        messages.append(text)


def wait_threads():
    """In tasks we need to wait while all threads to be completed
    because python-rq kill it's workers."""
    with _threads_lock:
        for thread in _threads:
            thread.join()
        _threads[:] = []


def clear_messages():
    messages[:] = []
