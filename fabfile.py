import time
import os

from fabric.api import local


def update_requirements():
    local('pip-compile --annotate requirements.in')
    local('pip-compile --annotate requirements-dev.in')


def _get_docker_command_old(name, ports=[], image='allmychanges.com'):
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
            '-e TOOLBAR_TOKEN=12345 '
#            '-e DEV_DOWNLOAD=yes '
            '--name {name} '
            '{image} ').format(
                name=name,
                image=image,
                ports=' '.join('-p ' + p for p in ports))

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

def compile_wheels():
    local('docker run --rm -v `pwd`:/wheels wheel-builder -r requirements-dev.txt')

def build_docker_image():
    local('docker build -t allmychanges.com .')

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
    name = 'manage.command.allmychanges.com' + args.replace(' ', '_')
    local(_get_docker_command(name) +
        '/env/bin/python /app/manage.py ' + args)

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


def versioneye():
    import requests

    API_KEY = '6456641e554ff23dcdc8'
    VERSIONEYE_SERVER = 'https://www.versioneye.com'
    PRJ_REQUIREMENTS_TXT = (
        ('56506b4253ef5f000c000c71', 'requirements.txt'),
        ('56506bdcd91d82000a000e0c', 'package.json'),)

    for project, filename in PRJ_REQUIREMENTS_TXT:
        url = '{server}/api/v2/projects/{project}?api_key={key}'.format(
            server=VERSIONEYE_SERVER,
            project=project,
            key=API_KEY)

        response = requests.post(
            url,
#            data=dict(name='project_file'),
            files=dict(project_file=open(filename, 'rb')))

        assert response.status_code == 201
