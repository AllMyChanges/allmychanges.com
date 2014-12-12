import re
import anyjson
import requests
import threading

from django.conf import settings

# these messages filled instead of sending
# during unittests
messages = []

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
    thread.daemon = True
    thread.start()

    if not settings.KATO_URL and not settings.SLACK_URL:
        messages.append(text)


def clear_messages():
    messages[:] = []
