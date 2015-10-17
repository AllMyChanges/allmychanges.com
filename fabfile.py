import time

from fabric.api import local


def update_requirements():
    local('pip-compile --annotate requirements.in')
    local('pip-compile --annotate requirements-dev.in')

def _get_docker_command(name, ports=[], image='allmychanges.com'):
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
            '{image} ').format(
                name=name,
                image=image,
                ports=' '.join('-p ' + p for p in ports))

def shell():
    local(_get_docker_command('shell.command.allmychanges.com') + (
        '/env/bin/python /app/manage.py '
        ' shell_plus'))

def dbshell():
    local('docker exec -it mysql.allmychanges.com mysql -ppassword allmychanges')

def get_db_from_production():
#    local('scp clupea:/mnt/yandex.disk/backups/mysql/allmychanges/latest.sql.bz2 dumps/')
#    local('bunzip2 dumps/latest.sql.bz2')
#    local('docker exec -ti mysql.allmychanges.com bash')
    local('docker exec mysql.allmychanges.com /dumps/restore.sh')

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
    local(_get_docker_command('manage.command.allmychanges.com') +
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


def drop_database():
    local('docker rm -fv mysql.allmychanges.com')

def create_database():
    start()
    get_db_from_production()
    manage('migrate')

def start():
    containers = _get_docker_containers()
    if 'mysql.allmychanges.com' in containers:
        local('docker start mysql.allmychanges.com')
    else:
        local('docker run --name mysql.allmychanges.com -v `pwd`/dumps:/dumps -e MYSQL_ROOT_PASSWORD=password -d mysql')
        print 'Waiting for mysql start'
        time.sleep(30)
        local('docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges')
        local('docker run --rm -it -v `pwd`:/app --link mysql.allmychanges.com allmychanges.com /env/bin/python /app/manage.py syncdb --migrate')

    if 'redis.allmychanges.com' in containers:
        local('docker start redis.allmychanges.com')
    else:
        local('docker run --name redis.allmychanges.com -d redis')


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
