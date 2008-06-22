#!/bin/bash

# Use this script to start the server as an unpriviledged user on Linux

PYCSUSER=www-pycs
BASH=/bin/bash
PYTHON=/usr/bin/python
PYCSBIN=/usr/lib/pycs/bin
LOGDIR=/var/log/pycs
ETCLOG=$LOGDIR/etc.log
ERRLOG=$LOGDIR/error.log

cd / && $PYTHON $PYCSBIN/pycs.py >> $ETCLOG 2>> $ERRLOG &
