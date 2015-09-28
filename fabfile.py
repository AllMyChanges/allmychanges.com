from fabric.api import local

def update_requirements():
    local('pip-compile --annotate requirements.in')
    local('pip-compile --annotate requirements-dev.in')

def _get_docker_command(name, ports=[]):
    return ('docker run '
            '--rm '
            '-t -i '
            '-v `pwd`:/app '
            '-v `pwd`/logs:/var/log/allmychanges '
            '-v `pwd`/tmp:/tmp/allmychanges '
            '--link mysql.allmychanges.com '
            '--link redis.allmychanges.com '
            '{ports} '
            '-e DEBUG=yes '
            '--name {name} '
            'allmychanges.com ').format(
                name=name,
                ports=' '.join('-p ' + p for p in ports))

def shell():
    local(_get_docker_command('shell.command.allmychanges.com') + (
        '/env/bin/python /app/manage.py '
        ' shell_plus'))

def runserver():
    local(_get_docker_command('runserver.command.allmychanges.com',
                              ports=['8000:8000']) + (
          '/env/bin/python /app/manage.py '
          'runserver 0.0.0.0:8000'))

def rqworker():
    local(_get_docker_command('rqworker.command.allmychanges.com') + (
        '/env/bin/python /app/manage.py '
        'rqworker '
        'default '
        'preview '))

def bash():
    local(_get_docker_command('bash.command.allmychanges.com') + 'bash')

def tail_errors():
    local("tail -f logs/django-root.log | jq 'if (.[\"@fields\"].level == \"WARNING\" or .[\"@fields\"].level == \"ERROR\") then . else 0 end | objects'")

def watch_on_static():
    local('node_modules/.bin/gulp')


def manage(args=''):
    local(_get_docker_command('tests.command.allmychanges.com') +
        '/env/bin/python /app/manage.py ' + args)

def test(args=''):
    local(_get_docker_command('tests.command.allmychanges.com') + (
        '/env/bin/nosetests ') + args)

def test2(args=''):
    local('nosetests ' + args)


def test_failed(args=''):
    local('nosetests --with-progressive --failed ' + args)


def test_failed2(args=''):
    local('nosetests --failed ' + args)

def coverage():
    local('nosetests --with-coverage --cover-package=allmychanges --cover-html --cover-erase --cover-inclusive --cover-html-dir=static/coverage')
    local('ssh back open http://art.dev.allmychanges.com:8000/static/coverage/index.html')


def kill_server():
    local('pkill -f runserver_plus')
