from fabric.api import local

def update_requirements():
    local('pip-compile --include-sources requirements.in')
    local('pip-compile --include-sources requirements-dev.in')

def shell():
    local('./manage.py shell_plus')


def test(args=''):
    local('nosetests --with-progressive ' + args)


def test_failed(args=''):
    local('nosetests --with-progressive --failed ' + args)


def coverage():
    local('nosetests --with-coverage --cover-package=allmychanges --cover-html --cover-erase --cover-inclusive --cover-html-dir=static/coverage')
    local('ssh back open http://art.dev.allmychanges.com:8000/static/coverage/index.html')


def kill_server():
    local('pkill -f runserver_plus')
