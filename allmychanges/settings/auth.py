AUTHENTICATION_BACKENDS = (
    'social.backends.twitter.TwitterOAuth',
    'social.backends.github.GithubOAuth2',
)


SOCIAL_AUTH_TWITTER_KEY        = 'zfUBhL9cF0B44r33AzszA'
SOCIAL_AUTH_TWITTER_SECRET     = 'v0rfjbdVUozKWjVSxQ0Wh5h0RKuZQy9CTIu35L9KLI'
SOCIAL_AUTH_GITHUB_KEY               = '7349d3551b5d86c85be1'
SOCIAL_AUTH_GITHUB_SECRET           = '6606dc0b084d8e304c0fbd5c794f4901c2785198'

LOGIN_REDIRECT_URL = '/after-login/'

