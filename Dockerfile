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
            mysql-client-core-5.5 \
            libmysqlclient-dev \
            libffi-dev \
            git \
            mercurial
COPY . /app
#RUN git clone git@github.com:svetlyak40wt/allmychanges.com.git /app

WORKDIR /app

RUN find . -name '*.pyc' -print0 | xargs -0 rm -f

RUN virtualenv --python=python2 /env
RUN /env/bin/pip install --use-wheel --no-index --find-links=wheelhouse -r requirements-dev.txt
RUN /env/bin/pip install -r requirements-from-git.txt
RUN /env/bin/pip install -e /app

ENV PATH=/env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin


#ENTRYPOINT ["./manage.py"]