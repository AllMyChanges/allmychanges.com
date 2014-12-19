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

def send(text):
    def remote_send():
        if settings.SLACK_URL:
            requests.post(settings.SLACK_URL,
                          data=anyjson.serialize(dict(text=text)))

        if settings.KATO_URL:
            kato_text = re.sub(ur'<(.*?)\|(.*?)>', ur'[\2](\1)', text)
            requests.post(settings.KATO_URL,
                          data=anyjson.serialize({'text': kato_text,
                                                  'renderer': 'markdown',
                                                  'from': 'bot'}))

    thread = threading.Thread(target=remote_send)
    thread.start()
    with _threads_lock:
        _threads.append(thread)

    if not settings.KATO_URL and not settings.SLACK_URL:
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
