#!/usr/bin/python

# Python Community Server
#
#     pycs_rewrite_handler.py: mod_rewrite-style URL rewriting
#
# Copyright (c) 2002, Phillip Pearson <pp@myelin.co.nz>
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


import re
import string
import http_server
from copy import copy

# This patches a set_header method into the http_request objects. This is
# butt-ugly code, but medusa doesn't allow a nice way to change what class
# to be used for http_request, so we better patch it than build our own
# full hierarchy of classes, just to overload some stuff. This method needs
# internal knowledge about http_request objects (it needs to know instance
# variables), and so this is bound to break sometime in the future!
def set_http_header( request, header, value ):
	request._header_cache[ string.lower( header ) ] = value
	h = header + ': '
	newheader = []
	found = 0
	for line in request.header:
		if line[ :len(h) ] == h:
			newheader.append( '%s: %s' % ( header, value ) )
			found = 1
		else:
			newheader.append( line )
	if not( found ):
		newheader.append( '%s: %s' % ( header, value ) )
	request.header = newheader

setattr( http_server.http_request, 'set_header', set_http_header )

HOST = re.compile(
	'Host: (.*)',
	re.IGNORECASE
	)

REQSPLITTER = re.compile(
	'http://([^/]+)(/.*)'
	)

class pycs_rewrite_handler:

	def __init__( self, set, rewriteMap=None ):

		self.set = set
		if rewriteMap == None:
			self.rewriteMap = []
		else:
			self.rewriteMap = rewriteMap
		self.rewriteMapBase = copy( self.rewriteMap )

	# reset rewriteMap to original value and add additional rules
	# (this is for reloading database based rewrite rules!)
	def resetRewriteMap( self, rewriteMap=None ):
		self.rewriteMap = copy( self.rewriteMapBase )
		if rewriteMap:
			self.rewriteMap.extend( rewriteMap )

	def rewriteUrl(self, fullUrl, quiet=0, request=None):
		lastOne = 0
		for rw in self.rewriteMap:
			logName, regex, repl, flags = rw
			oldUrl = fullUrl
			fullUrl = regex.sub( repl, fullUrl )
			redirect = None
			if regex.match( oldUrl ):
				if not quiet:
						print "rewriting " + oldUrl + " (with rule '" + logName + "', flags '" + flags + "')"
						print "       to " + fullUrl
				
				# Parse flags - see if we need to redirect or something
				flagList = re.split( ',', flags )
				#print "flags:",flagList
				for flag in flagList:
					if not len( flag ): continue
					f = flag[0]
					if f == 'R':
						if not quiet: print "redirect"
						m = re.compile( 'R=(\d+)' ).match( flag )
						if m:
							code = int( m.group( 1 ) )
							if not quiet: print "code",code
							redirect = ( fullUrl, code )
						else:
							redirect = ( fullUrl, 302 )
					elif f == 'L':
						if not quiet: print "stop processing redirects"
						lastOne = 1
					elif f == 'P':
						if not quiet: print "proxy"
						raise "Can't proxy, sorry!"
					elif f == 'H':
						m = re.compile( 'H(.*?)=(.*)' ).match( flag )
						if m:
							value = regex.sub( m.group(2), oldUrl )
							print "patch header %s to %s" % ( m.group(1), value )
							request.set_header( m.group(1), value )
					else:
						raise "Unknown flag '%s' in list '%s'" % ( flag, flags )
			
			if redirect:
				loc, code = redirect
				request['Location'] = loc
				request.error( code )
			
			if lastOne:
				# Stop processing commands
				break
		return fullUrl

	def match( self, request ):
	
		# Rewrite hook - figure out what the host is, and rewrite
		# the URL if required.  This is useful for virtual hosting,
		# Manila-style (foo.bar.com -> www.bar.com/foo)
	
		# Get path info
	
		path, params, query, fragment = request.split_uri()
		
		# Get hostname
		
		host = http_server.get_header_match( HOST, request.header )
		if host:
			if hasattr( request, 'host' ):
				print "request already has 'host' property!"
				print request.host
			request.host = host.groups()[0]
			print "host",request.host
		else:
			request.host = self.set.ServerHostname()

		# Make a URL out of it, rewrite as required, then unpack the URL
		
		fullUrl = 'http://%s%s' % ( request.host, path )

		fullUrl = self.rewriteUrl(fullUrl, request=request)
								
		newHost, newPath = REQSPLITTER.search( fullUrl ).groups()

		#print "new host",newHost,"and path",newPath
		
		# Dump the data back into the request object
		
		# I think we're the only module that looks at .host, but fix it up anyway
		request.host = newHost
		# default_handler looks at _split_uri
		request._split_uri = [newPath] + [ x for x in request._split_uri[1:] ]
		# xmlrpc_handler looks at uri
		request.uri = newPath

		# logging looks at the request - this should be patched, so
		# we log the actual requests and not the untranslated uris,
		# those should be better logged in a special rewrite.log!
		request.request = '%s %s HTTP/%s' % (
			request.command,
			request.uri,
			request.version
		)
		
		# And tell the HTTP server to continue as usual (with the newly rewritten path etc)
		
		return 0
		
