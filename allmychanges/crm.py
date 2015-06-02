# coding: utf-8
import arrow
from closeio_api import Client
from django.conf import settings


def _format_date(dt):
    return dt.strftime(u'%Y-%m-%dT%H:%M:%S')

def _get_user_tracks(user):
    tracks = user.changelogs.all().values_list('namespace', 'name')
    tracks = sorted(list(tracks))
    return map(u'{0[0]}/{0[1]}'.format, tracks)


def create(user):
    """Добавляет нашего пользователя в CRM базу."""
    emails = []
    if user.email:
        # добавляем, как office, а для вручную добавленного email
        # проставляем home
        emails.append(dict(email=user.email, type='office'))

    tracks = _get_user_tracks(user)
    custom = {'Login': user.username,
              'Profile': 'https://allmychanges.com/u/{0}/'.format(user.username),
              'Joined': _format_date(user.date_joined),
              'LastLogin': _format_date(user.last_login),
              'Changelogs': u', '.join(tracks) or None,
              'NumChangelogs': len(tracks)}

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


def update(user, crm_user):
    tracks = _get_user_tracks(user)
    churn_date = None
    latest_state = list(user.state_history.all().order_by('-id')[:1])
    if latest_state and latest_state[0].state == 'churned':
        non_churn_state = list(user.state_history.exclude(state='churned').order_by('-id')[:1])
        if non_churn_state:
            churn_date = arrow.get(non_churn_state[0].date).replace(days=1).date()

    data = {
        'custom.LastLogin': _format_date(user.last_login),
        'custom.Changelogs': u', '.join(tracks) or None,
        'custom.NumChangelogs': len(tracks),
        'custom.SendDigests': user.send_digest or 'not given',
        'custom.Churned': _format_date(churn_date) if churn_date else None,
    }
    
    api = Client(settings.CLOSEIO_KEY)
    api.put('lead/' + crm_user['id'], data=data)


def sync(user):
    """Создает или обновляет некоторые поля в CRM базе."""
    crm_user = get(user)
    if crm_user is None:
        create(user)
    else:
        update(user, crm_user)
