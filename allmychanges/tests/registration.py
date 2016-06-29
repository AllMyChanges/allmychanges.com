# coding: utf-8

from nose.tools import eq_
from .utils import check_status_code, create_user, refresh
from allmychanges import chat
from allmychanges.models import EmailVerificationCode

from django.core import mail
from django.test import Client
from django.core.urlresolvers import reverse


def test_user_creation_lead_to_chat_notification():
    chat.clear_messages()
    create_user('art')
    eq_(1, len(chat.messages))


def test_first_step_sends_email_with_email_validation_code():
    cl = Client()
    user = create_user('art')
    cl.login(username='art', password='art')

    eq_(0, EmailVerificationCode.objects.count())

    response = cl.post(reverse('first-step'),
                       dict(email='unittest@allmychanges.com',
                            timezone='UTC'))
    check_status_code(302, response)

    eq_('http://testserver' + reverse('second-step'), response['Location'])
    eq_(1, EmailVerificationCode.objects.count())
    user = refresh(user)
    assert user.email_verification_code is not None
    eq_(1, len(mail.outbox))


def test_verification_code():
    cl = Client()
    user = create_user('art')
    code = EmailVerificationCode.new_code_for(user)
    url = reverse('verify-email', kwargs=dict(code=code.hash))

    eq_(False, user.email_is_valid)

    response = cl.get(url)
    check_status_code(200, response)

    user = refresh(user)
    eq_(True, user.email_is_valid)


def test_email_is_required_in_account_settings():
    # email field is required now.
    # here we check if error message is shown on the page
    # when email is not given

    cl = Client()
    user = create_user('art')
    cl.login(username='art', password='art')

    url = reverse('account-settings')
    response = cl.post(
        url,
        dict={}
    )
    check_status_code(200, response)
    assert 'There is some error in the form data' in response.content
    with open('/tmp/allmychanges/response.html', 'w') as f:
        f.write(response.content)
    assert 'We need your email to deliver fresh release notes.' in response.content
