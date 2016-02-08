allmychanges.com
================

package.json notes
------------------

* jquery нужен, само собой
* jquery.cookie нужен, чтобы вынимать csrftoken из куки и засовывать в HTTP заголовок
* Модули babel-core и webpack были добавлены на верхний уровнем модулем babel-loader.
* react и react-dom были добавлены модулем react-mdl.
* priorityqueuejs я использую, чтобы приоретизировать показ плашек с помощью intro.js
* react-tabs мне нужны чтобы на странице настройки пакета показывать в табиках доступные опции
после того, как changelog был или не был найден.
ставится с https://github.com/svetlyak40wt/react-tabs, потому что мне пришлось поправить версию
reactjs в зависимостях с 0.13 на 0.14.
* style-loader нужен чтобы импортировать стили внутри javascript компонент
* css-loader нужен чтобы загружать css внутри javascript
* stylus-loader для загрузки stylus шаблонов
* gulp-rename gulp-uglify - чтобы собирать [минифицированную версию js](https://github.com/gulpjs/gulp/blob/master/docs/recipes/minified-and-non-minified.md)
* gulp-concat - для того, чтобы объединить воедино кучу js файлов, которые я не могу подключить с помощью require внутри своих компонент
* bower, всё-таки пришлось поставить, потому что не всё можно использовать через npm
например lodash для UserStory нельзя так поставить

bower modules
-------------

* lodash - нужен для UserStory
* typehead.js - нужен для автокомлита в главной строке поиска
* pubsub-js - чтобы показывать всплывашки и делать другие штуки по событию

Как запустить всё под Docker
----------------------------

### Новая дока

Это все про запуск новой инсталяции в деве под 1.9 докером.

```
# это скопирует снапшот базы с прода
fab create_database
# в одной консоли
fab runserver
# во второй консоли
fab rqworker
```

### Устаревшая дока


```
docker run --name mysql.allmychanges.com -e MYSQL_ROOT_PASSWORD=password -d mysql
или
docker start mysql.allmychanges.com
если контейнер уже запускался

docker run --name redis.allmychanges.com -d redis
или
docker start redis.allmychanges.com

docker exec -i -t mysql.allmychanges.com mysqladmin drop   -ppassword allmychanges
docker exec -i -t mysql.allmychanges.com mysqladmin create -ppassword allmychanges

docker run --rm -t -i -v `pwd`:/app --link mysql.allmychanges.com allmychanges.com /env/bin/python /app/manage.py syncdb

fab runserver

```


A project for Django Dash 2013

How to setup
------------

    $ sudo apt-get install mysql-server redis-server python-dev libxml2-dev libxslt1-dev logtail python-virtualenv python-pip python-mysqldb mercurial memcached libmemcached-tools libmysqlclient-dev
    $ sudo apt-get install python-qt4 xvfb # to render changelog images
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

   npm install


Clearing RQ queue
-----------------

1. Start `rq-dashboard`
2. Go to http://art.dev.allmychanges.com:9181/default
3. Press `Empty`


Using amch to import requirements.txt
-------------------------------------

    cat requirements.txt| grep -v '^-e' | sed -e 's/\([^=]\+\).*/python,\1/' -e '1 i\namespace,name' | head | amch import


How to transfer autocomplete data
---------------------------------

    # skate
    mysqldump -u allmychanges -pallmychanges  allmychanges_art allmychanges_autocompletedata allmychanges_autocompleteword2 allmychanges_autocompleteword2_data_objects | bzip2 > autocomplete.sql.bz2

    # local
    scp skate:allmychanges.com/autocomplete.sql.bz2 ./
    scp allmychanges.com/autocomplete.sql.bz2 clupea:allmychanges.com/

    # clupea
    bzcat autocomplete.sql.bz2| mysql -u allmychanges -pallmychanges allmychanges


Interesting projects
--------------------

* Command-line utility, showing changelog of npm packages: https://github.com/dylang/changelog
* A tool for updating project changelogs and package.json files for new releases: https://github.com/defunctzombie/changelog
