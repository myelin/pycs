#!/bin/bash

# Use this script to start the server as an unpriviledged user on Linux

PYCSUSER=www-radio
BASH=/bin/bash
PYTHON=/usr/bin/python
PYCSHOME=/home/www-radio
LOGFILE=/home/phil/PyCS/safe_server_log.txt

cd $PYCSHOME && su $PYCSUSER -s $BASH "$PYTHON $PYCSHOME/pycs.py" >> $LOGFILE &
