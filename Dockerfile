FROM ubuntu:14.04
MAINTAINER Alexander Artemenko <svetlyak.40wt@gmail.com>

# Prepare
RUN apt-get update && apt-get install -y build-essential python-dev python-virtualenv libssl-dev libxml2-dev libxslt1-dev mercurial libmysqlclient-dev libffi-dev git mercurial
COPY . /app
#RUN git clone git@github.com:svetlyak40wt/allmychanges.com.git /app

WORKDIR /app

RUN virtualenv --python=python2 /env
RUN /env/bin/pip install -r requirements-dev.txt
RUN /env/bin/pip install -e /app




