# coding: utf-8

import os
import re
import time

from invoke import task, run
#invoke.tasks.Task
from common_tasks import (
    update_requirements,
    make_dashed_aliases,
    get_current_version)


VERSION = get_current_version() + '-dev'


def get_docker_client():
    import docker
    import os
    cert_path = os.environ['DOCKER_CERT_PATH']

    client_cert = os.path.join(cert_path, 'cert.pem')
    # пробовал использовать для валидации сертификат,
    # но почему-то не срабатывает. Жалуется на
    # то что 192.168.*.* не соответствует localhost.
    # Надо разбираться.
    # ca_cert = os.path.join(cert_path, 'ca.pem')
    client_key = os.path.join(cert_path, 'key.pem')

    tls_config = docker.tls.TLSConfig(
        client_cert=(client_cert, client_key),
        verify=False,
    )
    url = os.environ['DOCKER_HOST'].replace('tcp://', 'https://')
    return docker.Client(base_url=url, tls=tls_config)



def _get_docker_containers():
    cl = get_docker_client()
    containers = cl.containers(all=True)
    containers = [c['Names'][0].strip('/') for c in containers]
    return containers


def get_docker_networks():
    cl = get_docker_client()
    networks = cl.networks()
    networks = [c['Name'] for c in networks]
    return networks


@task
def check_versions():
    import requests

    API_KEY = '6456641e554ff23dcdc8'
    VERSIONEYE_SERVER = 'https://www.versioneye.com'
    PRJ_REQUIREMENTS_TXT = (
        ('56506b4253ef5f000c000c71', 'requirements.txt'),
        ('56506bdcd91d82000a000e0c', 'package.json'),)

    for project, filename in PRJ_REQUIREMENTS_TXT:
        printed_project_name = False

        url = '{server}/api/v2/projects/{project}?api_key={key}'.format(
            server=VERSIONEYE_SERVER,
            project=project,
            key=API_KEY)

        response = requests.post(
            url,
#            data=dict(name='project_file'),
            files=dict(project_file=open(filename, 'rb')))

        assert response.status_code == 201
        data = response.json()
        for dep in data['dependencies']:
            if dep['outdated']:
                if not printed_project_name:
                    printed_project_name = True
                    print filename

                print ('  {0[prod_key]}'
                       '{0[comparator]}'
                       '{0[version_requested]}'
                       ' has newer version {0[version_current]}{1}').format(
                           dep,
                           'has security issues'
                           if dep['security_vulnerabilities'] else '')


@task
def create_docker_network():
    if 'amch' not in get_docker_networks():
        run('docker network create amch')


@task(create_docker_network)
def start_databases():
    containers = _get_docker_containers()
    if 'mysql.allmychanges.com' in containers:
        run('docker start mysql.allmychanges.com')
    else:
        run('docker run --net amch --name mysql.allmychanges.com -v `pwd`/dumps:/dumps -e MYSQL_ROOT_PASSWORD=password -d mysql')
        print 'Waiting for mysql start'
        time.sleep(30)
        run('docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges')
        run('docker run --rm -it -v `pwd`:/app --net amch allmychanges.com /env/bin/python /app/manage.py syncdb --migrate')

    if 'redis.allmychanges.com' in containers:
        run('docker start redis.allmychanges.com')
    else:
        run('docker run --net amch --name redis.allmychanges.com -d redis')


@task
def build_wheels():
    run('docker run '
        '--rm '
        '-v `pwd`:/wheels '
        '40ants/wheel-builder '
        '--wheel-dir wheelhouse '
        '-r requirements/dev.txt')


@task
def build_image(dev=True):
    tag = 'localhost:5000/allmychanges.com:' + VERSION
    run('docker build -t {0} .'.format(tag))
    print 'Built', tag


@task
def push_image():
    tag = 'localhost:5000/allmychanges.com:' + VERSION
    tag = tag.replace('-dev', '')

    run('docker build -t {} .'.format(tag))
    run('docker push ' + tag)
    print 'Pushed', tag



def _get_docker_command(name, ports=[], image=None, rm=True, debug=True):
    command = ['docker run',]

    if image is None:
        image = os.environ.get(
            'IMAGE',
            'localhost:5000/allmychanges.com:' + VERSION)

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


@task
def manage(args, ports=[], name=None):
    if name is None:
        if len(args) < 40:
            hashed_args = re.sub(ur'[ \:/]+', '_', args)
        else:
            hashed_args = '.long.command'
        name = 'manage.command.allmychanges.com' + hashed_args

    command = _get_docker_command(
        name,
        ports=ports) + \
        '/env/bin/python /app/manage.py ' + args
    print command
    run(command, pty=True)


@task
def runserver():
    # сейчас почему-то сломано завершение процесса по Ctrl-C
    # следим за этим в https://github.com/pyinvoke/invoke/issues/315
    # и https://github.com/pyinvoke/invoke/issues/327
    manage('runserver 0.0.0.0:80',
           name='runserver.command.allmychanges.com',
           ports=['80:80'])


@task
def rqworker():
    manage('rqworker default preview',
           name='rqworker.command.allmychanges.com')


@task
def shell():
    manage('shell_plus',
           name='shell.command.allmychanges.com')

@task
def test(case='', failed=False, verbose=False):
    command = ['/env/bin/nosetests']

    for name in ('verbose', 'failed'):
        if locals().get(name):
            command.append('--' + name)

    command.append(case)

    run(_get_docker_command('tests.command.allmychanges.com') +
        ' '.join(command))


@task
def create_database():
    run('docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges',
        pty=True)

@task
def drop_database():
    run('docker exec -it mysql.allmychanges.com mysqladmin -ppassword drop allmychanges',
        pty=True)
    create_database()

@task
def bash():
    command = _get_docker_command('bash') + 'bash'
    print command
    run(command, pty=True)


@task
def get_latest_db():
    run('scp clupea:/mnt/yandex.disk/backups/mysql/allmychanges/latest.sql.bz2 dumps/')


@task
def restore_db():
    run('docker exec mysql.allmychanges.com /dumps/restore.sh')


make_dashed_aliases(locals().values())
