# Paths used in PyCS
#
# AFAIK these conform to the Filesystem Hierarchy Standard.
# http://www.pathname.com/fhs/
#
# Please tell me if they don't ;-)

# The root of it all (no trailing '/').
# This is set automatically by the install Makefile
ROOTDIR = '{{PREFIX}}'

import os.path

# Config files
CONFDIR = os.path.join( ROOTDIR, 'etc/pycs' )

# Read-only stuff
RODIR = os.path.join( ROOTDIR, 'usr/lib/pycs' )

# Logging
LOGDIR = os.path.join( ROOTDIR, 'var/log/pycs' )
ACCESSLOG = os.path.join( LOGDIR, 'access.log' )

# Runtime information
RUNDIR = os.path.join( ROOTDIR, 'var/run/pycs' )
PIDFILE = os.path.join( RUNDIR, 'pycs.pid' )

# Writeable area for us to store web pages, comments etc
VARDIR = os.path.join( ROOTDIR, 'var/lib/pycs' )

# Persistent data store (DB)
DATADIR = os.path.join( VARDIR, 'data' )

# Web pages
WEBDIR = os.path.join( VARDIR, 'www' )

# Scripts
MODDIR = os.path.join( VARDIR, 'modules' )

if __name__ == '__main__':
	# we are being called by make during installation to replace the prefix with
	# something meaningful.

	import sys, os.path
	me, prefix = sys.argv
	print open( me ).read().replace( '{{PREFIX}}', os.path.abspath( prefix ) )
