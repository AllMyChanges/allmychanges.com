FROM python:2-alpine3.11
LABEL MAINTAINER="Alexander Artemenko <svetlyak.40wt@gmail.com>"

# libmysqlclient-dev replaced by mariadb-dev
# removed python-virtualenv
#TODO: python-qt4 for makescreenshot (546ce6c4b25e84fed70732669d00aa9ac1c372d8)
# gcc for cffi
# musl-dev for https://stackoverflow.com/a/30873179/5155484
RUN apk add --no-cache \
            openssl-dev \
            libxml2-dev \
            libxslt-dev \
            mysql-client \
            mariadb-dev \
            libffi-dev \
            musl-dev \
            git \
            mercurial \
            gcc \
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
