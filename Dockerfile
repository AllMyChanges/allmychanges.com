FROM ubuntu:14.04
LABEL MAINTAINER="Alexander Artemenko <svetlyak.40wt@gmail.com>"

# Prepare
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
            build-essential \
            python-dev \
            python-virtualenv \
            libssl-dev \
            libxml2-dev \
            libxslt1-dev \
            mysql-client-core-5.5 \
            libmysqlclient-dev \
            libffi-dev \
            git \
            mercurial \
            python-qt4 \
            xvfb

#COPY ./wheelhouse /wheelhouse
COPY ./requirements/dev.txt /requirements.txt
COPY ./requirements/from-git.txt /requirements-from-git.txt

# disable wheelhouse for Drone builds
# RUN pip install --use-wheel --no-index --find-links=/wheelhouse -r /requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt
RUN pip install -r /requirements-from-git.txt

COPY . /app
WORKDIR /app

RUN find . -name '*.pyc' -print0 | xargs -0 rm -f
RUN pip install -e /app

ENV PATH=/env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

COPY ./configs/.pdbrc.py /root/

#ENTRYPOINT ["./manage.py"]
