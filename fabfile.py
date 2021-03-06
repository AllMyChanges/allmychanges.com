# coding: utf-8

import os
import time
import re

from fabric.api import local


def _get_docker_command(name, ports=[], image=None, rm=True, debug=True):
    command = ['docker run',]

    if image is None:
        image = os.environ.get('IMAGE', 'allmychanges.com')

    if rm:
        command.append('--rm')

    command.extend([
            '-t -i',
            '-v `pwd`:/app',
            '-v `pwd`/logs:/var/log/allmychanges',
            '-v `pwd`/tmp:/tmp/allmychanges',
            '--net amch',
            ' '.join('-p ' + p for p in ports)])

    if debug:
        command.append('-e DEBUG=yes')
#            '-e DEV_DOWNLOAD=yes'

    command.extend([
            '-e REDIS_HOST=redis.allmychanges.com',
            '-e MYSQL_HOST=mysql.allmychanges.com',
            '-e MYSQL_DATABASE=allmychanges',
            '-e MYSQL_USER=root',
            '-e MYSQL_PASSWORD=password',
            '-e TOOLBAR_TOKEN=12345',
            '--name',
            name,
            image])

    command = ' '.join(command)
    return command + ' '


def build_docker_image(version):
    assert version
    tag = 'localhost:5000/allmychanges.com:' + version
    local('docker build -t {0} .'.format(tag))


def upload_docker_image(version):
    assert version
    tag = 'localhost:5000/allmychanges.com:' + version
    local('docker build -t {} .'.format(tag))
    local('docker push ' + tag)


def shell():
    # используем shell2 потому что иначе возникает ошибка
    # Error response from daemon: Could not find container for entity id 3f21744e9eddc17e7a4a32ac61993f5fbe3e85e0da908c1d7781d0eb4262d35c
    # она должна быть исправлена в версии докера 1.10
    # https://github.com/docker/docker/pull/16032
    # и описана тут
    # https://github.com/docker/docker/issues/17691
    local(_get_docker_command('shell2.command.allmychanges.com') + (
        '/env/bin/python /app/manage.py '
        ' shell_plus'))

def dbshell():
    local('docker exec -it mysql.allmychanges.com mysql -ppassword allmychanges')

def get_db_from_production():
    local('scp clupea:/mnt/yandex.disk/backups/mysql/allmychanges/latest.sql.bz2 dumps/')
    local('rm -fr dumps/latest.sql')
    local('bunzip2 dumps/latest.sql.bz2')
#    local('docker exec -ti mysql.allmychanges.com bash')
    local('docker exec mysql.allmychanges.com /dumps/restore.sh')

def runserver():
    local(_get_docker_command('runserver.command.allmychanges.com',
                              ports=['8000:8000']) + (
          '/env/bin/python /app/manage.py '
          'runserver 0.0.0.0:8000'))

def rungunicorn():
    # sudo docker run --rm -ti -e MYSQL_HOST=192.241.207.244 -e DJANGO_SETTINGS_MODULE=allmychanges.settings.production -p 8000:8000 --entrypoint gunicorn edited:latest allmychanges.wsgi:application --bind 0.0.0.0:8000 --access-logfile -
    local(_get_docker_command(
        'runserver.command.allmychanges.com',
        debug=False,
        ports=['8000:8000'])
          + (
              'gunicorn '
              'allmychanges.wsgi:application '
            '--bind 0.0.0.0:8000 '
              '--access-logfile -'))

def rqworker():
    local(_get_docker_command('rqworker.command.allmychanges.com') + (
        '/env/bin/python /app/manage.py '
        'rqworker '
        'default '
        'preview '))

def bash(args=''):
    if args == 'edit':
        rm = False
    else:
        rm = True

    local(_get_docker_command('bash.command.allmychanges.com', rm=rm) + 'bash')

def tail_errors():
    local("tail -f logs/django-root.log | jq 'if (.[\"@fields\"].level == \"WARNING\" or .[\"@fields\"].level == \"ERROR\") then . else 0 end | objects'")

def manage(args=''):
    if len(args) < 40:
        hashed_args = re.sub(ur'[ \:/]+', '_', args)
    else:
        hashed_args = '.long.command'
    name = 'manage.command.allmychanges.com' + hashed_args
    local(_get_docker_command(name) +
        '/env/bin/python /app/manage.py ' + args)

def dev_extract_history(repo_name):
    name = 'dev_extract_history.command.allmychanges.com'
    local(_get_docker_command(name) +
          '/env/bin/python /app/manage.py dev_extract_history /tmp/allmychanges/' + repo_name)

def test(args=''):
    local(_get_docker_command('tests.command.allmychanges.com') + (
        '/env/bin/nosetests ') + args)

def test2(args=''):
    local('nosetests ' + args)


def test_failed(args=''):
    local(_get_docker_command('tests.command.allmychanges.com') + (
        '/env/bin/nosetests --with-progressive --failed ') + args)

def test_failed2(args=''):
    local(_get_docker_command('tests.command.allmychanges.com') + (
        '/env/bin/nosetests --failed ') + args)

def coverage():
    local('nosetests --with-coverage --cover-package=allmychanges --cover-html --cover-erase --cover-inclusive --cover-html-dir=static/coverage')
    local('ssh back open http://art.dev.allmychanges.com:8000/static/coverage/index.html')


def drop_database():
    local('docker rm -fv mysql.allmychanges.com')

def create_database():
    start()
    get_db_from_production()
    manage('migrate')

def start():
    # до выполнения надо создать сеть amch
    # docker network create amch
    containers = _get_docker_containers()
    if 'mysql.allmychanges.com' in containers:
        local('docker start mysql.allmychanges.com')
    else:
        local('docker run --net amch --name mysql.allmychanges.com -v `pwd`/dumps:/dumps -e MYSQL_ROOT_PASSWORD=password -d mysql')
        print 'Waiting for mysql start'
        time.sleep(30)
        local('docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges')
        local('docker run --rm -it -v `pwd`:/app --net amch allmychanges.com /env/bin/python /app/manage.py syncdb --migrate')

    if 'redis.allmychanges.com' in containers:
        local('docker start redis.allmychanges.com')
    else:
        local('docker run --net amch --name redis.allmychanges.com -d redis')


def stop():
    local('docker rm --force -v rqworker.command.allmychanges.com; true')
    local('docker rm --force -v runserver.command.allmychanges.com; true')
    local('docker stop mysql.allmychanges.com; true')
    local('docker stop redis.allmychanges.com; true')


def delete_containers():
    containers = (
        'rqworker.command.allmychanges.com',
        'runserver.command.allmychanges.com',
        'mysql.allmychanges.com',
        'redis.allmychanges.com')

    for container in containers:
        local('docker rm --force -v {0}; true'.format(container))


def _get_docker_containers():
    import docker
    import os
    cert_path = os.environ['DOCKER_CERT_PATH']

    tls_config = docker.tls.TLSConfig(
        client_cert=(os.path.join(cert_path, 'cert.pem'),
                     os.path.join(cert_path, 'key.pem')),
        verify=False,
    )
    cl = docker.Client(base_url=os.environ['DOCKER_HOST'].replace('tcp://', 'https://'),
                tls=tls_config)

    containers = cl.containers(all=True)
    containers = [c['Names'][0].strip('/') for c in containers]
    return containers
