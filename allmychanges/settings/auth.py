AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'social.backends.twitter.TwitterOAuth',
    'social.backends.github.GithubOAuth2',
)

# OAuth2
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 365 # 1 year

SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']

# https://apps.twitter.com/
SOCIAL_AUTH_TWITTER_KEY        = 'zfUBhL9cF0B44r33AzszA'
SOCIAL_AUTH_TWITTER_SECRET     = 'v0rfjbdVUozKWjVSxQ0Wh5h0RKuZQy9CTIu35L9KLI'

# https://github.com/settings/applications
SOCIAL_AUTH_GITHUB_KEY               = '7349d3551b5d86c85be1'
SOCIAL_AUTH_GITHUB_SECRET           = '6606dc0b084d8e304c0fbd5c794f4901c2785198'

LOGIN_REDIRECT_URL = '/after-login/'


SOCIAL_AUTH_PIPELINE = (
    # adds key 'details' with information about user, taken from a backend
    'social.pipeline.social_auth.social_details',
    # adds key uid, taken from backend
    'social.pipeline.social_auth.social_uid',
    # checks if authentication is allowed and trows exception AuthForbidden
    'social.pipeline.social_auth.auth_allowed',
    # gets a social profile from db and checks if it is not associated with another user
    # populates 'social', 'user', 'is_new' and 'new_association' keys
    'social.pipeline.social_auth.social_user',
    # chooses username for a new user and stores it in a 'username' key
    'social.pipeline.user.get_username',
    # calls strategy's create_user if there isn't user yet
    # created user is stored in 'user' key, and 'is_new' key become True
    'social.pipeline.user.create_user',
    # adds web/allmychanges package
    'allmychanges.auth.pipeline.add_default_package',
    # associates social profile with current user
    'social.pipeline.social_auth.associate_user',
    # loads extra data from the backend and stores it in a social profile
    'social.pipeline.social_auth.load_extra_data',
    # updates user model with data from provider
    # sensitive fields could be protected using 'PROTECTED_USER_FIELDS'
    # settings
    # WARNING, these fields will be overwritten at each login
    'social.pipeline.user.user_details',
)
