#!/usr/bin/python

# Python Community Server
#
#     pycs.py: Main code file
#     Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
#                     and Michael Hay <Michael.Hay@hds.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of 
# the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


print "[Loading server]"

# Get the path right
import os
import os.path
import sys
scriptDir = os.path.abspath( os.path.dirname( sys.argv[0] ) )
sys.path += [
	scriptDir,
	os.path.join( scriptDir, 'medusa' ),
	os.path.join( scriptDir, 'metakit' )
]
print sys.path

import pycs_paths

# System & web server modules
import asyncore
import http_server
import filesys
import re
import time

# Internal modules
import pycs_settings
import daemonize

# HTTP handlers
import default_handler
import pycs_rewrite_handler
import pycs_module_handler
import pycs_xmlrpc_handler
import pycs_auth_handler

# XML-RPC handlers
import xmlStorageSystem
import radioCommunityServer
import weblogUpdates

# Logging
import logger
import status_handler

def terminate (signal, param):
	"""Signal handler for the pycs daemon.  Applicable
	only to those systems implementing POSIX signals.
	"""

	ctime = time.asctime( time.localtime( time.time() ) )
	print "[Received signal", signal, "terminating]", ctime 
	os.remove( pycs_paths.PIDFILE )
	sys.exit( 0 )
	
def install_handlers ():
	import signal
	#install default signal profile
	signal.signal( signal.SIGTTOU, signal.SIG_IGN )
	signal.signal( signal.SIGTTIN, signal.SIG_IGN )
	signal.signal( signal.SIGCHLD, signal.SIG_IGN )
	signal.signal( signal.SIGTSTP, terminate )
	signal.signal( signal.SIGTERM, terminate )
	signal.signal( signal.SIGINT, terminate )

print "[Loaded]"

if __name__ == '__main__':

	# Become a daemon if we're running on a POSIX platform.
	# TODO: run as a Windows service on NT.
	if os.name == 'posix':
		
		# Install signal handlers
		install_handlers()
	
		# Become a UNIX daemon
		daemonize.become_daemon(
			pycs_paths.ROOTDIR,
			os.path.join( pycs_paths.LOGDIR, 'etc.log' ),
			os.path.join( pycs_paths.LOGDIR, 'error.log' )
		)
	
		# Write the presently running pid to a pid file
		# which will typically be used to stop and get status of
		# the pycs daemon.
		my_pid = os.getpid()
		pid_file = open( pycs_paths.PIDFILE, 'w' )
		pid_file.write( "%d" % my_pid )
		pid_file.close()

	# Get config
	set = pycs_settings.Settings()

	# Make URL rewriter
	rewriteMap = []
	rewriteFn = os.path.join( pycs_paths.CONFDIR, 'rewrite.conf' )
	try:
		import os
		os.stat( rewriteFn )
	except:
		raise "Can't read URL rewriting config file " + rewriteFn
	execfile( rewriteFn )
	
	rw_h = pycs_rewrite_handler.pycs_rewrite_handler( set, rewriteMap )

	# Make GET handler	
	fs = filesys.os_filesystem( pycs_paths.WEBDIR )
	default_h = default_handler.default_handler( fs )
	if os.path.isfile( os.path.join( pycs_paths.CONFDIR, 'users.conf' ) ):
		# Add auth wrapper
		default_h = pycs_auth_handler.pycs_auth_handler( set, default_h )
	
	# Make XML-RPC handler
	rpc_h = pycs_xmlrpc_handler.pycs_xmlrpc_handler( set )
	
	# Make xmlStorageSystem XML-RPC handler
	rpc_xss_h = xmlStorageSystem.xmlStorageSystem_handler( set )
	rpc_h.AddNamespace( 'xmlStorageSystem', rpc_xss_h )
	
	# Make radioCommunityServer XML-RPC handler
	rpc_rcs_h = radioCommunityServer.radioCommunityServer_handler( set )
	rpc_h.AddNamespace( 'radioCommunityServer', rpc_rcs_h )
	
	# Make weblogUpdates XML-RPC handler
	rpc_wu_h = weblogUpdates.weblogUpdates_handler( set )
	rpc_h.AddNamespace( 'weblogUpdates', rpc_wu_h )
	
	# Make handler for /system
	mod_h = pycs_module_handler.pycs_module_handler( set )
	if os.path.isfile( os.path.join( pycs_paths.CONFDIR, 'users.conf' ) ):
		# Add auth wrapper
		mod_h = pycs_auth_handler.pycs_auth_handler( set, mod_h )
	
	# Make logger
	accessLog = logger.rotating_file_logger( pycs_paths.ACCESSLOG, None, 100*1024 )
	print "logging to",pycs_paths.ACCESSLOG
	logger = status_handler.logger_for_status( accessLog )
	
	# Make web server
	hs = http_server.http_server( '', set.ServerPort(), None, logger )
	hs.server_name = set.conf['serverhostname']

	# become the PyCS user
	if os.name == 'posix':
		if hasattr( os, 'seteuid' ):
			# look in ~medusa/patches for {set,get}euid.
			import pwd
			[uid, gid] = pwd.getpwnam( set.conf['serveruser'] )[2:4]
			os.setegid (gid)
			os.seteuid (uid)
		else:
			print "WARNING: Can't reduce privileges; server is running as the superuser"
	
	hs.install_handler( default_h )
	hs.install_handler( mod_h )
	hs.install_handler( rpc_h )
	hs.install_handler( rw_h )
	#hs.install_handler( log_h )
	
	print "[Server started]"
	asyncore.loop()
