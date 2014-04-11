allmychanges.com
================

A project for Django Dash 2013

How to setup
------------

    $ sudo apt-get install mysql-server redis-server python-dev libxml2-dev libxslt1-dev logtail python-virtualenv python-pip python-mysqldb mercurial
    $ chmod +x scripts/create-env.sh
    $ scripts/create-env.sh
    $ source env/bin/activate
    $ echo "SECRET_KEY = '$(python -c 'import os, sha; print sha.sha(os.urandom(100)).hexdigest()')'" > secure_settings.py
    $ chmod +x manage.py
    $ sudo mkdir -p /var/log/allmychanges
    $ sudo chmod 777 /var/log/allmychanges
    $ sudo mkdir -p /var/log/logster
    $ sudo chmod 777 /var/log/logster
    $ sudo mkdir -p /var/run/logster
    $ sudo chmod 777 /var/log/logster
    $ ./manage.py syncdb --migrate
    $ ./manage.py runserver 0.0.0.0:8000
    $ # and in other console
    $ ./manage.py rqworker

Maybe you need to create mysql database before `./manage.py syncdb --migrate`. Run `mysql -uroot`:

    mysql> CREATE DATABASE allmychanges CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    mysql> GRANT ALL ON allmychanges.* TO `allmychanges`@`localhost` IDENTIFIED BY 'allmychanges';

In production you will need additional steps like:

   $ sudo mkdir -p /var/www/.ssh
   $ sudo chown www-data:www-data /var/www/.ssh
   $ sudo -u www-data ssh-keygen
   $ cat /var/www/.ssh/id_rsa.pub
   $ echo "Now create a new GitHub account and put this ssh key there."


How to run tmux for development
-------------------------------

   env/bin/tmuxp load .tmuxp.yaml

or

   a tmux


Installing Stylus for developement
----------------------------------

   sudo apt-get install software-properties-common
   sudo add-apt-repository ppa:chris-lea/node.js
   sudo apt-get update
   sudo apt-get install python-software-properties python g++ make nodejs