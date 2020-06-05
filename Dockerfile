FROM python:2-slim
LABEL MAINTAINER="Alexander Artemenko <svetlyak.40wt@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
            build-essential \
            python-dev \
            python-virtualenv \
            libssl-dev \
            libxml2-dev \
            libxslt1-dev \
            mariadb-client \
            default-libmysqlclient-dev \
            libffi-dev \
            git \
            mercurial \
            python-qt4 \
            xvfb

COPY ./requirements/dev.txt /requirements.txt
COPY ./requirements/from-git.txt /requirements-from-git.txt

RUN pip install --upgrade pip
RUN pip install -r /requirements.txt
RUN pip install -r /requirements-from-git.txt
