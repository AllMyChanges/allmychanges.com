FROM ubuntu:14.04
MAINTAINER Alexander Artemenko <svetlyak.40wt@gmail.com>

# Prepare
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update && \
    apt-get install -y \
            build-essential \
            python-dev \
            python-virtualenv \
            libssl-dev \
            libxml2-dev \
            libxslt1-dev \
            mercurial \
            mysql-client-core-5.5 \ # to make dbshell available
            libmysqlclient-dev \
            libffi-dev \
            git \
            mercurial
COPY . /app
#RUN git clone git@github.com:svetlyak40wt/allmychanges.com.git /app

WORKDIR /app

RUN virtualenv --python=python2 /env
RUN /env/bin/pip install -r requirements-dev.txt
RUN /env/bin/pip install -r requirements-from-git.txt
RUN /env/bin/pip install -e /app

ENV PATH=/env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin


ENTRYPOINT ["./manage.py"]