# Paths used in PyCS
#
# AFAIK these conform to the Filesystem Hierarchy Standard.
# http://www.pathname.com/fhs/
#
# Please tell me if they don't ;-)


# Config files
CONFDIR = '/etc/pycs'


# Read-only stuff
RODIR = '/usr/lib/pycs'


# Logging
LOGDIR = '/var/log/pycs'
ACCESSLOG = LOGDIR + '/access.log'


# Writeable area for us to store web pages, comments etc
VARDIR = '/var/lib/pycs'

# Persistent data store (DB)
DATADIR = VARDIR + '/data'

# Web pages
WEBDIR = VARDIR + '/www'

# Scripts
MODDIR = VARDIR + '/modules'