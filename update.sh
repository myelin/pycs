#!/bin/bash

kill `cat /home/www-pycs/var/run/pycs/pycs.pid`
make install
python /home/www-pycs/usr/lib/pycs/bin/pycs.py
