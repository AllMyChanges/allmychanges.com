allmychanges.com
================

Развертывание dev-окружения
---------------------------

В девеловерской среде всё разворачивается в отдельных docker-контейнерах.
В них надо поднять mysql, redis и в отдельных контейнерах будут стартовать
все management команды типа runserver. Отличие от продакшн-окружения только
в том, что в деве внтурь докер-контейнера пробрасывается всё дерево с
исходниками, и когда они меняются, происходит reload кода, контейнер пересобирать
и перезапускать не надо.

Если рабочая машинка с Linux, то лучше поставить docker на неё, если нет, то
докер надо запускать в VirtualBox, дальше будет часть про то, как это сделать на OSX.

### Поднимаем docker на OSX

Сначала надо установить docker клиент и docker-machine через [homebrew][]:

```
$ brew install docker docker-machine
```

Если у вас ещё не установлен VirtualBox, то его нужно поставить либо вручную,
либо через [brew cask][cask]:

```
$ brew cask install virtualbox
```

Далее, создаем виртуалку, в которой будет бежать docker:

```
$ docker-machine create --driver virtualbox amch
```

Когда команда отработает, у вас в VirtualBox появится новая виртуалка
с именем amch и на ней будет установлен docker.

Чтобы работать с этим докер-демоном из консоли OSX, нужно установить
некоторые переменные окружения. Какие? Это подскажет команда:

```
$ docker-machine env amch
export DOCKER_TLS_VERIFY="1"
export DOCKER_HOST="tcp://192.168.99.100:2376"
export DOCKER_CERT_PATH="/Users/art/.docker/machine/machines/amch"
export DOCKER_MACHINE_NAME="amch"
# Run this command to configure your shell:
# eval "$(docker-machine env amch)"
```

Чтобы не устанавливать их вручную, можно либо прописать `eval "$(docker-machine env amch)"`
в `~/.bashrc`, либо использовать [autoenv][] и прописать её в файлик .env внутри репозитория
AllMyChanges.

В любом случае, надо проверить, работает ли клиент докера:

```
$ docker version
Client:
Version:      1.9.1
API version:  1.21
Go version:   go1.5.1
Git commit:   a34a1d5
Built:        Sat Nov 21 00:49:19 UTC 2015
OS/Arch:      darwin/amd64

Server:
Version:      1.9.1
API version:  1.21
Go version:   go1.4.3
Git commit:   a34a1d5
Built:        Fri Nov 20 17:56:04 UTC 2015
OS/Arch:      linux/amd64
```

Если клиент не находит сервера, то вместо информации о сервере он выведет что-то
вроде:

```
Cannot connect to the Docker daemon. Is the docker daemon running on this host?
```

Проблема тут в том, что не установлены те самые переменные окружения.

Если виртуалка не запущена, то клиент подольше потупит, и сообщение будет другое:

```
Cannot connect to the Docker daemon. Is the docker daemon running on this host?
```

Тогда надо стартовать виртуалку командой:

```
docker-machine start amch
```

В принципе, и эту строку можно прописать в локальный `.env` файлик для [autoenv][].


### Стартуем mysql и redis

Для старта разных команд в проекте использовался fabric, но сейчас всё
переписывается на invoke.

Обычно я ставлю всякие python либы и утилиты прямо внутри дерева проекта,
с созданную через virtualenv папку `env`.

Создаем окружение:

```
$ virtualenv env
$ pip install -U pip
$ pip install -r requirements/host.txt
```

Окружение надо активировать:

```
$ source env/bin/activate
```

Эту команду тоже удобно добавить в `.env` файл. Только лучше добавлять как:

```
if [ -e env ]; then
  source env/bin/activate
fi
```

После активации окружения, вам должна стать доступна команда `inv`,
которая запускает таски, описанные в `tasks.py`.

Чтобы создать контейнеры с базами, запускаем:

```
$ inv start_databases
```

Если всё прошло как надо, то команда `docker ps` должна показать нам два запущенных
контейнера:

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
6277dc3c8bf3        redis               "/entrypoint.sh redis"   7 seconds ago       Up 7 seconds        6379/tcp            redis.allmychanges.com
06aa8ed1bea8        mysql               "/entrypoint.sh mysql"   10 minutes ago      Up 15 seconds       3306/tcp            mysql.allmychanges.com
```

Теперь надо накатить миграции
-----------------------------

Для этого надо как-то запустить `./manage.py` migrate внутри контейнера с кодом
AllMyChanges. Но контейнера у нас нет, поэтому сначала его надо построить.

При сборке образа, чтобы pip быстрее отрабатывал, у нас используется
предварительная компиляция wheels. Для этого, запустите команду:

```
$ inv build-wheels
```

Затем нужно собрать docker образ:

```
$ inv build-image
```

И создать базу:

```
$ inv create-database
$ inv manage migrate
```

Миграцию приходится запускать дважды, потому что первый раз там
вылазит какая-то Integrity error.

Осталось запустить вебсервер
----------------------------

```
$ inv runserver
```

И асинхронный воркер
--------------------

```
$ inv rqworker
```

Да открыть в браузере результат
-------------------------------

Для того, чтобы посмотреть, что там поднялось в докере, надо получить адрес
виртуалки:

```
$ docker-machine ip amch
192.168.99.100
```

Этот урл надо прописать в `/etc/hosts`, добавив такую строчку:

```
192.168.99.100 dev.allmychanges.com
```


Старые доки, которые надо актуализировать или удалить
-----------------------------------------

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


[homebrew]: http://brew.sh
[cask]: http://caskroom.io
[autoenv]: https://github.com/kennethreitz/autoenv
