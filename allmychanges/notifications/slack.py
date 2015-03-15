import requests
import anyjson


def send(url, text):
    data = {'text': text,
            'username': 'AllMyChanges.com'}
    requests.post(url, data=anyjson.serialize(data))
