Tracked events
==============

We are tracking what user is doing during his life.

IMPORTANT! When you add item into this list, please
add this action into models.ACTIVE_USER_ACTIONS

Here is a list of event which are tracked:

* track: 'User tracked changelog:123'
* untrack: 'User untracked changelog:123'
* track-allmychanges: 'User tracked our project\'s changelog.'
* untrack-allmychanges: 'User untracked our project\'s changelog.'
* landing-track: 'User has tracked changelog:123'
* landing-ignore: 'User has ignored changelog:123'
* landing-digest-view: 'User opened a landing page with digest.'
* account-created: 'User created account'
  Used in `AfterLoginView` if it was called in 60 second interval
  after user joined the service.
* login: 'User logged in'
  Used in `AfterLoginView` if it was called after 60 second interval
  from `date_joined`.
* digest-view: 'User viewed the digest'
* package-view: 'User opened package /u/allmychanges/web/allmychanges/' or 'User opened changelog:123'
* package-create: 'User created changelog:123'
* package-edit: 'User edited changelog:123'
* profile-view: 'User opened his profile settings'
* profile-update: 'User saved his profile settings'
* digest-sent: 'We send user an email with digest'
  This event is created by management command send_digests.
* email-digest-open:  'User opened digest email'
* email-digest-click: 'User clicked a link "{0}" in digest email'


To track new events
-------------------

1. Add new event into the list above.
2. Use this code like this to track it:
    ```
    UserHistoryLog.write(
        request.user,
        request.light_user,
        'landing-track',
        'User has tracked changelog:{0}'.format(track_id))
    ```
