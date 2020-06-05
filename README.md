# allmychanges.com


## Dev environment

In a development environment, everything is deployed in separate docker containers.
In them you need to raise mysql, redis and will start in separate containers
all management commands like runerver. The difference from the production environment is only
in the fact that in the maiden inside the docker container the whole tree is thrown with
source codes, and when they change, reload the code, the container is reassembled
and do not need to restart.

If a working machine with Linux, then it is better to put docker on it, if not, then
the docker must be launched in VirtualBox, the next part will be about how to do this on OSX.

### Raise docker on OSX

First you need to install the docker client and docker-machine via [homebrew][]:

```bash
$ brew install docker docker-machine
```

If you have not yet installed VirtualBox, then you need to install it either manually,
either via [brew cask][cask]:

```bash
$ brew cask install virtualbox
```

Next, create a virtual machine in which docker will run:

```bash
$ docker-machine create --driver virtualbox amch
```

When the team completes, a new virtual box will appear in your VirtualBox
with the name amch and docker will be installed on it.

To work with this docker daemon from the OSX console, you need to install
some environment variables. What kind? This will tell the command:

```bash
$ docker-machine env amch
export DOCKER_TLS_VERIFY="1"
export DOCKER_HOST="tcp://192.168.99.100:2376"
export DOCKER_CERT_PATH="/Users/art/.docker/machine/machines/amch"
export DOCKER_MACHINE_NAME="amch"
# Run this command to configure your shell:
# eval "$(docker-machine env amch)"
```

In order not to install them manually, you can either register `eval" $(docker-machine env amch)"`
in `~/.bashrc`, or use [autoenv][] and write it to the .env file inside the repository
AllMyChanges.

In any case, you need to check if the docker client works:

```bash
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

If the client does not find the server, then instead of information about the server, it will display something
like:

```
Cannot connect to the Docker daemon. Is the docker daemon running on this host?
```

The problem here is that the same environment variables are not set.

If the virtual machine is not running, then the client will wait longer and the message will be different:

```
Cannot connect to the Docker daemon. Is the docker daemon running on this host?
```

Then you need to start the virtual machine with the command:

```
docker-machine start amch
```

In principle, this line can also be written into the local `.env` file for [autoenv][].


### Starting mysql and redis

The project used fabric to start different teams, but now everything
Corresponds to invoke.

I usually put all sorts of python libs and utilities right inside the project tree,
with the `env` folder created through virtualenv.

Create an environment:

```bash
$ virtualenv env
$ pip install -U pip
$ pip install -r requirements/host.txt
```

The environment must be activated:

```bash
$ source env/bin/activate
```

This command is also convenient to add to the `.env` file. It’s only better to add as:

```
if [ -e env ]; then
  source env/bin/activate
fi
```

After activating the environment, the `inv` command should be available to you,
which runs the tasks described in `tasks.py`.

To create containers with databases, run:

```bash
$ inv start_databases
```

If everything went as it should, then the `docker ps` command should show us two running
container:

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
6277dc3c8bf3        redis               "/entrypoint.sh redis"   7 seconds ago       Up 7 seconds        6379/tcp            redis.allmychanges.com
06aa8ed1bea8        mysql               "/entrypoint.sh mysql"   10 minutes ago      Up 15 seconds       3306/tcp            mysql.allmychanges.com
```

Now we need to roll migration
-----------------------------

To do this, somehow run `./manage.py` migrate inside the container with the code
AllMyChanges. But we do not have a container, so we must first build it.

When assembling the image so that pip runs faster, we use
wheels precompilation. To do this, run the command:

```bash
$ inv build-wheels
```

Then you need to build a docker image:

```bash
$ inv build-image
```

And create a base:

```bash
$ inv create-database
$ inv manage migrate
```

Migration has to be run twice because the first time there
climbs out some Integrity error.

It remains to start the web server
----------------------------

```bash
$ inv runserver
```

And asynchronous worker
--------------------

```bash
$ inv rqworker
```

Yes, open the result in a browser
-------------------------------

In order to see what went up in the docker, you need to get the address
virtual computers:

```
$ docker-machine ip amch
192.168.99.100
```

This url must be written in `/etc/hosts`, adding the following line:

```
192.168.99.100 dev.allmychanges.com
```

After that, you can open <http://dev.allmychanges.com> in your browser and it will appear
AllMyChanges interface.


How to get data from production and pour local database
--------------------------------------------------------

If there is a database dump from production, then uploading it to the local database is easy and simple.
It is enough to put the dump in the dumps directory, so that the file name is
`dumps/latest.tar.bz2` and after that you need to run the command:

```
inv restore-db
```

**Warning** previous data will be erased.


[homebrew]: http://brew.sh
[cask]: http://caskroom.io
[autoenv]: https://github.com/kennethreitz/autoenv


How to create and run migrations
-----------------------------------

Create:
```
inv manage makemigrations
```

Run:
```
inv manage migrate
```

How to run tests
-------------------

Very simple:

```
inv test
```

It is also useful to run not all tests, but only flawed ones:

```
inv test --failed
```
