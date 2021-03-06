# coding: utf-8

import os
import re
import time

from invoke import task, run
#invoke.tasks.Task
from common_tasks import (
    update_requirements,
    make_dashed_aliases)

def get_docker_client():
    import docker
    import os
    cert_path = os.environ.get('DOCKER_CERT_PATH')
    if cert_path:

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

    else:
        return docker.Client()



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

#@task
#def push_to_amch():
    #run('time pip2amch --tag allmychanges.com requirements/production.txt | amch push')
    # import requirements
    # import tablib

    # with open('requirements/production.txt') as f:
    #     lines = f.readlines()
    #     lines = (line.split('#', 1)[0] for line in lines)
    #     lines = (line.strip() for line in lines)
    #     reqs = '\n'.join(lines)

    # parsed = requirements.parse(reqs)
    # data = tablib.Dataset()
    # data.headers = ['namespace', 'name', 'version', 'tag']

    # def extract_version(specs):
    #     for spec, version in specs:
    #         if spec == '==':
    #             return version
    #     return ''

    # for item in parsed:
    #     data.append(
    #         (
    #             'python',
    #             item.name,
    #             extract_version(item.specs),
    #             'allmychanges.com'
    #         )
    #     )

    # with open('amch-data.csv', 'w') as f:
    #     f.write(data.csv)

    # run('amch push --filename amch-data.csv', pty=True)
#    run('rm -fr amch-data.csv')


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
        run('docker run --net amch --name mysql.allmychanges.com '
            '-v `pwd`/dumps:/dumps '
            '-e MYSQL_ROOT_PASSWORD=password '
            '-d mysql '
            ' --character-set-server=utf8mb4 '
            '--collation-server=utf8mb4_unicode_ci')

        print 'Waiting for mysql start'
        time.sleep(30)
        run('docker exec -it mysql.allmychanges.com mysqladmin -ppassword create allmychanges')
        #run('docker run --rm -it -v `pwd`:/app --net amch allmychanges.com /env/bin/python /app/manage.py syncdb')

    # Commented while I'm not experimenting with postgres

    # if 'postgres.allmychanges.com' in containers:
    #     run('docker start postgres.allmychanges.com')
    # else:
    #     run('docker run --net amch --name postgres.allmychanges.com -v `pwd`/dumps:/dumps -e POSTGRES_PASSWORD=password -d postgres')
    #     print 'Waiting for postgres start'
    #     # time.sleep(30)
    #     # run('docker exec -it postgres.allmychanges.com postgresadmin -ppassword create allmychanges')
    #     # run('docker run --rm -it -v `pwd`:/app --net amch allmychanges.com /env/bin/python /app/manage.py syncdb --migrate')


    if 'redis.allmychanges.com' in containers:
        run('docker start redis.allmychanges.com')
    else:
        run('docker run --net amch --name redis.allmychanges.com -d redis')


def _get_docker_command(name, ports=[], image=None, rm=True, debug=True):
    command = ['docker run',]

    if image is None:
        image = os.environ.get('IMAGE', DEV_TAG)

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


@task(start_databases)
def runserver():
    # сейчас почему-то сломано завершение процесса по Ctrl-C
    # следим за этим в https://github.com/pyinvoke/invoke/issues/315
    # и https://github.com/pyinvoke/invoke/issues/327
    manage('runserver 0.0.0.0:80',
           name='runserver.command.allmychanges.com',
           ports=['80:80'])


@task(start_databases)
def rqworker():
    manage('rqworker default preview',
           name='rqworker.command.allmychanges.com')


@task(start_databases)
def shell():
    manage('shell_plus',
           name='shell.command.allmychanges.com')

@task(start_databases)
def test(case='', failed=False, verbose=False, attr=None):
    command = ['/env/bin/nosetests']

    for name in ('verbose', 'failed'):
        if locals().get(name):
            command.append('--' + name)

    if case:
        if ':' not in case:
            # replace last dot to make nosetests happy
            # and allow just copy&paste test names from
            # stdout
            case = ':'.join(case.rsplit('.', 1))

        command.append(case)

    if attr:
        command.append('-a ' + attr)

    run(_get_docker_command('tests.command.allmychanges.com') +
        ' '.join(command))

make_dashed_aliases(locals().values())
