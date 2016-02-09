from invoke import task, run


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
