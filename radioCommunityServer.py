#!/usr/bin/python

# Python Community Server
#
#     radioCommunityServer.py: XML-RPC handler for radioCommunityServer.*
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


"""radioCommunityServer XML-RPC Handler

This file handles XML-RPC requests for the radioCommunityServer namespace.

"""

class radioCommunityServer_handler:

	"radioCommunityServer XML-RPC functions"

	def __init__( self, set ):
		self.set = set



	def call( self, method, params ):
		print "RCS method",method #,"params",params
		
		handlers = {
			'getInitialResources': self.getInitialResources,
			}
		
		if len( method ) == 0:
			raise "radioCommunityServer method not specified"
		
		base = method[0]
		if handlers.has_key( base ):
			return handlers[base]( method[1:], params )
		
		raise "radioCommunityServer method not found"



	def getInitialResources( self, method, params ):
		if method != []: raise "Namespace not found"
		if params != (): raise "Too many parameters"
	
		return {
			'commentsPageUrl': self.set.ServerUrl() + 'system/comments.py',
			}
