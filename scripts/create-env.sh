#!/bin/bash

ENVDIR=env

if [ ! -e $ENVDIR/bin/python ]; then
#    env3/bin/virtualenv --python=/usr/bin/python --system-site-packages --distribute $ENVDIR
    virtualenv --python=/usr/bin/python $ENVDIR
    $ENVDIR/bin/pip install -U pip
    $ENVDIR/bin/pip install -U -r requirements.txt
    $ENVDIR/bin/pip install -e `pwd`

    fi
