# Paths used in PyCS
#
# AFAIK these conform to the Filesystem Hierarchy Standard.
# http://www.pathname.com/fhs/
#
# Please tell me if they don't ;-)

# The root of it all (no trailing '/').  If you want to install PyCS
# in a user directory, set this to '/home/foo'.
ROOTDIR = ''


# Config files
CONFDIR = ROOTDIR + '/etc/pycs'


# Read-only stuff
RODIR = ROOTDIR + '/usr/lib/pycs'


# Logging
LOGDIR = ROOTDIR + '/var/log/pycs'
ACCESSLOG = LOGDIR + '/access.log'


# Writeable area for us to store web pages, comments etc
VARDIR = ROOTDIR + '/var/lib/pycs'

# Persistent data store (DB)
DATADIR = VARDIR + '/data'

# Web pages
WEBDIR = VARDIR + '/www'

# Scripts
MODDIR = VARDIR + '/modules'
