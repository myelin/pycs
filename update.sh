#!/bin/bash

kill `ps ax | grep "pycs.py" | grep -v "grep" | perl -pe 's/(\d+).*/\1/'`
make install
/usr/lib/pycs/startserver.sh
