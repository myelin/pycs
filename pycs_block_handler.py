#!/usr/bin/python

# Python Community Server
#
#     pycs_block_handler.py: blocking handler for disabled users
#
# Copyright (c) 2002, Georg Bauer <gb@murphy.bofh.ms>
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

USERRE = re.compile( r'/users/([0-9]+)' )

class pycs_block_handler:

	def __init__( self, set ):

		self.set = set

	# check wether we should handle this URL
	def match( self, request ):
	
		path, params, query, fragment = request.split_uri()

		# this handler needs standard users/<usernum> paths, so it
		# must beinstalled so that first the rewrite handler runs!

		umatch = USERRE.match( path )
		if umatch:
			try:	
				user = self.set.User( umatch.group( 1 ) )
				# check wether the user is disabled, if yes
				# catch this call
				if user and user.disabled:
					return 1
			except:
				pass
		return 0

	# handle this URL by passing it along to continue_request
	def handle_request( self, request ):
		self.continue_request( None, request )

	# handle this URL by just delivering a "disabled" document
	def continue_request( self, data, request ):
		path, params, query, fragment = request.split_uri()

		fullurl = 'http://%s%s' % ( request.host, path )
		request['Content-Type'] = 'text/html'
		page = {'title': 'URL disabled'}
		page['body'] = """
			The URL <a href="%s">%s</a> is disabled for administrative reasons.
			Please contact the systems administrator if you think
			that this is an error. The administrator can be reached
			at the <a href="%s">homepage</a> of this server.
			""" % ( fullurl, fullurl, self.set.ServerUrl() )
		s = self.set.Render( page )
		request['Content-Length'] = len( s )
		request.push( s )
		request.done()

