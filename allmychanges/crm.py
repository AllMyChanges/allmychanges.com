# coding: utf-8

from closeio_api import Client
from django.conf import settings


def create(user):
    """Добавляет нашего пользователя в CRM базу."""
    emails = []
    if user.email:
        emails.append(dict(email=user.email, type='office'))
    custom = {'Login': user.username,
              'Profile': 'https://allmychanges.com/u/{0}/'.format(user.username)}

    auth_templates = {'twitter': ('Twitter', 'https://twitter.com/{username}'),
                      'github': ('GitHub', 'https://github.com/{username}/')}
    auth = user.social_auth.all().values_list('provider', flat=True)
    for item in auth:
        title, tmpl = auth_templates.get(item)
        custom[title] = tmpl.format(username=user.username)


    if settings.DEBUG:
        custom['DEBUG'] = 'true'

    data= {'contacts': [{'name': user.username,
                         'emails': emails}],
           'custom': custom}

    api = Client(settings.CLOSEIO_KEY)
    api.post('lead', data=data)


def get(user):
    """Возвращает CRM пользователя если он есть в базе CRMю
    """
    api = Client(settings.CLOSEIO_KEY)
    results = api.get('lead', data=dict(query='custom.login=' + user.username))
    if results.get('data'):
        return results['data'][0]


def update(user):
    pass


def sync(user):
    """Создает или обновляет некоторые поля в CRM базе."""
    crm_user = get(user)
    if crm_user is None:
        create(user)
    else:
        update(user)
