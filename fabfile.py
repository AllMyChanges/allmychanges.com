from fabric.api import local

def update_requirements():
    local('pip-compile --include-sources requirements.in')
    local('pip-compile --include-sources requirements-dev.in')

    
