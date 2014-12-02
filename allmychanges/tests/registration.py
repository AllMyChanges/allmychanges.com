# coding: utf-8

from nose.tools import eq_
from .utils import create_user
from allmychanges import chat


def test_user_creation_lead_to_chat_notification():
    chat.clear_messages()
    create_user('art')
    eq_(1, len(chat.messages))
