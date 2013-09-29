#!/bin/bash

# this script updates application in production

BASEDIR=$(dirname $(dirname $0))

pushd "$BASEDIR" > /dev/null

git pull
env/bin/pip install -r requirements.txt
env/bin/pip install -e .

sudo -u www-data env/bin/python manage.py syncdb --migrate --settings=allmychanges.settings.production
sudo mkdir -p static
sudo chown www-data:www-data static
yes yes | sudo -u www-data env/bin/python manage.py collectstatic  --settings=allmychanges.settings.production

sudo cp configs/upstart.conf /etc/init/allmychanges.conf
sudo service allmychanges restart
sudo cp configs/nginx.conf /etc/nginx/sites-enabled/allmychanges.conf
sudo service nginx restart

sudo cp configs/rqworker-upstart.conf /etc/init/allmychanges-rqworker.conf
sudo service allmychanges-rqworker restart

mkdir -p data
sudo chown -R www-data:www-data data
