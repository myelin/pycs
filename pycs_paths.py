# Paths used in PyCS
#
# AFAIK these conform to the Filesystem Hierarchy Standard.
# http://www.pathname.com/fhs/
#
# Please tell me if they don't ;-)

# The root of it all (no trailing '/').
# This is set automatically by the install Makefile
ROOTDIR = '{{PREFIX}}'

import os, os.path

def first_of(*files):
	"look for the first file in a list that exists"
	for f in files:
		if os.path.exists(f):
			return f
	return files[0]

# see if we're running out of the source distribution
if ROOTDIR == '{{PRE' + 'FIX}}':
	ROOTDIR = os.path.abspath('root')
	for x in ("", "var", "var/log", "var/log/pycs", "var/run", "var/run/pycs", "var/lib", "var/lib/pycs", "var/lib/pycs/data", "var/lib/pycs/www"):
		d = os.path.join(ROOTDIR, x)
		if not os.path.exists(d):
			os.mkdir(d)

# Config files
CONFDIR = os.path.join( ROOTDIR, 'etc/pycs' )
if not os.path.isdir(CONFDIR): CONFDIR=os.path.normpath('.')
PYCS_CONF = first_of(os.path.join( CONFDIR, "pycs.conf" ), os.path.join(CONFDIR, 'pycs.conf.default'))
REWRITE_CONF = first_of(os.path.join(CONFDIR, "rewrite.conf"), os.path.join(CONFDIR, "rewrite.conf.default"))

# Read-only stuff
RODIR = os.path.join( ROOTDIR, 'usr/lib/pycs' )
if not os.path.isdir(RODIR): RODIR='.'

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
if not os.path.exists(MODDIR): MODDIR=os.path.normpath('./modules')

if __name__ == '__main__':
	# we are being called by make during installation to replace the prefix with
	# something meaningful.

	import sys, os.path
	me, prefix = sys.argv
	print open( me ).read().replace( '{{PREFIX}}', os.path.abspath( prefix ) )
