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
]
print sys.path

import pycs_paths

# System & web server modules
import asyncore
import http_server
import monitor
import filesys
import re
import time

# Internal modules
import pycs_settings
import daemonize

# HTTP handlers
import default_handler
import pycs_rewrite_handler
import pycs_block_handler
import pycs_module_handler
import pycs_xmlrpc_handler
import pycs_auth_handler
import pycs_webauth_handler

# XML-RPC handlers
import xmlStorageSystem
import radioCommunityServer
import weblogUpdates
import pycsAdmin
import accessRestrictions

# Logging
import logger
import status_handler

# Translation handling
import pycs_translation

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

# a really ugly hack to patch my own log version into the http_request :-)
# this is done so that we can produce a combined log instead of the common
# log. This gives referrer and user agent information. It's ugly, as we patch
# the method definition instead of overloading the classes, but since medusa
# doesn't give us an easy way to specify the class used for http_requests, it's
# better than the alternative. Don't do things like this at home, kids!
def mylog (self, bytes):
	self.channel.server.logger.log (
		self.get_header('X-Request-For') or self.channel.addr[0],
		'- - [%s] "%s" %d %d "%s" "%s"\n' % (
			time.strftime('%d/%b/%Y:%H:%M:%S %z'),
			self.request,
			self.reply_code,
			bytes,
			self.get_header('referer') or '-',
			self.get_header('user-agent') or '-'
		)
	)

setattr(http_server.http_request, 'log', mylog)

# this patches the unresolved_logger class to don't log the stupid ':', because
# combined logs don't log the port, only the IP of the remote host
def log_unresolved (self, ip, message):
	self.logger.log ('%s %s' % (ip, message))

setattr(logger.unresolving_logger, 'log', log_unresolved)

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

	# Figure out if we need to use authentication
	if os.path.isfile( os.path.join( pycs_paths.CONFDIR, 'users.conf' ) ):
		import authorizer
		auth = authorizer.authorizer()
	else:
		auth = None

	# Get config
	set = pycs_settings.Settings(authorizer=auth)

	pycs_translation.translation(set.Language()).install()

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
	set.SetRewriteHandler(rw_h)

	set.reloadAliases( rw_h )
	
	# Make URL blocker
	bl_h = pycs_block_handler.pycs_block_handler( set )

	# Make GET handler	
	fs = filesys.os_filesystem( pycs_paths.WEBDIR )
	default_h = default_handler.default_handler( fs )

	if set.authorizer is not None:
		# Add auth wrapper
		default_h = pycs_auth_handler.pycs_auth_handler( set, default_h, set.authorizer )

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
	
	# Make pycsAdmin XML-RPC handler
	rpc_padm_h = pycsAdmin.pycsAdmin_handler( set )
	rpc_h.AddNamespace( 'pycsAdmin', rpc_padm_h )

	# Make accessRestrictions XML-RPC handler
	rpc_ar_h = accessRestrictions.accessRestrictions_handler( set )
	rpc_h.AddNamespace( 'accessRestrictions', rpc_ar_h )
	set.SetAccessRestrictionsHandler(rpc_ar_h)
	
	# Make handler for /system
	mod_h = pycs_module_handler.pycs_module_handler( set )
	if os.path.isfile( os.path.join( pycs_paths.CONFDIR, 'users.conf' ) ):
		# Add auth wrapper
		mod_h = pycs_auth_handler.pycs_auth_handler( set, mod_h, set.authorizer )
	
	# add the webauth wrapper (handles accessRestriction restrictions)
	default_h = pycs_webauth_handler.pycs_webauth_handler( set, default_h, rpc_ar_h )

	# Make logger
	accessLog = logger.rotating_file_logger( pycs_paths.ACCESSLOG, None, 1024*1024 )
	print "logging to",pycs_paths.ACCESSLOG
	logger = status_handler.logger_for_status( accessLog )

	# Make web server
	hs = http_server.http_server( '', set.ServerPort(), None, logger )
	hs.server_name = set.conf['serverhostname']

	ms = None
	if set.conf.has_key( 'monitorport' ):
		port = int( set.conf['monitorport'] )
		if set.conf.has_key( 'monitorpassword' ):
			pwd = set.conf['monitorpassword']
			ms = monitor.secure_monitor_server( pwd, '', port )
		else:
			ms = monitor.monitor_server( '', port )

	# become the PyCS user
	if os.name == 'posix':
		try:
			# look in ~medusa/patches for {set,get}euid.
			import pwd
			[uid, gid] = pwd.getpwnam( set.conf['serveruser'] )[2:4]
			os.setegid (gid)
			os.seteuid (uid)
		except:
			import traceback
			traceback.print_exc()
			print "WARNING: Can't reduce privileges; server is running as the superuser"
	
	# Make a status handler
	status_h = status_handler.status_extension( [ hs ] )
	
	hs.install_handler( default_h )
	hs.install_handler( mod_h )
	hs.install_handler( rpc_h )
	hs.install_handler( bl_h )
	hs.install_handler( status_h )
	#hs.install_handler( log_h )
	# install rewrite handler last, so that it is processed first
	hs.install_handler( rw_h )
	
	print "[Server started]"
	asyncore.loop()
