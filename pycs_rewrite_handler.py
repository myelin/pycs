import re
import default_handler
import http_server

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

		for rw in self.rewriteMap:
			logName, regex, repl, flags = rw
			oldUrl = fullUrl
			fullUrl = regex.sub( repl, fullUrl )
			redirect = None
			if oldUrl != fullUrl:
				print "rewriting " + oldUrl + " (with rule '" + logName + "', flags '" + flags + "')"
				print "       to " + fullUrl
				
				# Parse flags - see if we need to redirect or something
				flagList = re.split( ',', flags )
				#print "flags:",flagList
				for flag in flagList:
					if not len( flag ): continue
					f = flag[0]
					if f == 'R':
						print "redirect"
						m = re.compile( 'R=(\d+)' ).match( flag )
						if m:
							code = int( m.group( 1 ) )
							print "code",code
							redirect = ( fullUrl, code )
						else:
							redirect = ( fullUrl, 302 )
					elif f == 'P':
						print "proxy"
						raise "Can't proxy, sorry!"
					else:
						raise "Unknown flag '%s' in list '%s'" % ( flag, flags )
			
			if redirect:
				loc, code = redirect
				request['Location'] = loc
				request.error( code )
								
		newHost, newPath = REQSPLITTER.search( fullUrl ).groups()

		#print "new host",newHost,"and path",newPath
		
		# Dump the data back into the request object
		
		# I think we're the only module that looks at .host, but fix it up anyway
		request.host = newHost
		# default_handler looks at _split_uri
		request._split_uri = [newPath] + [ x for x in request._split_uri[1:] ]
		# xmlrpc_handler looks at uri
		request.uri = newPath
		
		# And tell the HTTP server to continue as usual (with the newly rewritten path etc)
		
		return 0
		