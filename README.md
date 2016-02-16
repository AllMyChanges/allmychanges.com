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

После этого можно открыть в браузере <http://dev.allmychanges.com> и покажется
интерфейс AllMyChanges.


Как получить данные с продакшена и налить локальную базу
--------------------------------------------------------

Если есть дамп базы с продакшена, то залить его в локальную базу легко и просто.
Достаточно положить дамп в директорию dumps, так, чтобы имя файло было
`dumps/latest.tar.bz2` и после этого надо запустить команду:

```
inv restore-db
```

**Внимание** предыдущие данные будут при этом затерты.


[homebrew]: http://brew.sh
[cask]: http://caskroom.io
[autoenv]: https://github.com/kennethreitz/autoenv


Как создавать и накатывать миграции
-----------------------------------

Создавать:
```
inv manage makemigrations
```

Накатывать:
```
inv manage migrate
```

Как запускать тесты
-------------------

Очень просто:

```
inv test
```

Бывает так же полезно запускать не все тесты, а только сфейлившиеся:

```
inv test --failed
```
