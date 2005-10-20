#!/usr/bin/python

# Python Community Server
#
#     weblogUpdates.py: XML-RPC handler for weblogUpdates.*
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


"""weblogUpdates XML-RPC Handler

This file handles XML-RPC requests for the weblogUpdates namespace.

Kind of like http://www.weblogs.com/RPC2 and RCS

"""

import os
import sys
import re
import string

import pycs_settings
import xmlrpclib


class weblogUpdates_handler:
	
	"weblogUpdates XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		
		
		
	def call( self, method, params ):
		print "WU method",method #,"params",params
		
		handlers = {
			'ping': self.ping,
			}
		
		if len( method ) == 0:
			raise "weblogUpdates method not specified"
		
		base = method[0]
		if handlers.has_key( base ):
			return handlers[base]( method[1:], params )
		
		raise "weblogUpdates method not found"



	def ping( self, method, params ):
		if method != []: raise "Namespace not found"

		print "params:",params		
		blogName = params[0]
		blogUrl = params[1]
		category = 'none'
		if len( params ) > 2:
			print "got extra params:",params[2:]
			if len( params ) > 3:
				category = params[3]
				if category != 'none':
					return {
						'flError': xmlrpclib.True,
						'message': 'Sorry, "%s" isn\'t an allowed category name' % ( category, ),
					}
		
		if type(blogName) == type(u''):
			blogName = blogName.encode(self.set.DocumentEncoding())
		print "got a ping from '%s' at '%s'" % ( blogName, blogUrl )

		self.set.AddUpdatePing(blogName, blogUrl)
		
		return {
			'flError': xmlrpclib.False,
			'message': 'Thanks for the ping!',
			}
		

if __name__=='__main__':
	# Testing
	s = xmlrpclib.Server( 'http://www.pycs.net/RPC2' )
	print s.weblogUpdates.ping( 'Test blog', 'http://www.pycs.net/' )
	
