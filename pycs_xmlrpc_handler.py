#!/usr/bin/python

# Python Community Server
#
#     pycs_xmlrpc_handler.py: XML-RPC handler
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


"""PyCS XML-RPC Handler

This file handles XML-RPC requests.  It matches the URL '/RPC2'.  Each XML-RPC
root namespace (e.g. 'xmlStorageSystem') is handled by a separate class.  Use
.AddNamespace() to do this.

"""

import sys
import string

import xmlrpc_handler
import xmlrpclib




class pycs_xmlrpc_handler( xmlrpc_handler.xmlrpc_handler ):

	def __init__( self, set ):
		self.set = set
		self.namespaces = {}
		

	# a hack to introduce a default encoding, if one is set in the
	# server to circumvent encoding problems introduced by Radio
	def continue_request( self, data, request ):
		data = self.set.PatchEncodingHeader( data )
		xmlrpc_handler.xmlrpc_handler.continue_request( self, data, request )

		
	def AddNamespace( self, name, handler ):
	
		"""Add a new namespace, e.g. xmlStorageSystem, to the handler,
		so it can accept incoming XML-RPC calls"""
		
		self.namespaces[ name ] = handler
	
	
	
	def call( self, method, params ):
		#print "method",method,"params",params
		
		# Split name from "one.two.three" to ['one', 'two', 'three']
		qualifiedName = string.split( method, '.' )
				
		if len( qualifiedName ) == 0:
			raise "Namespace required for method '%s'" % ( qualifiedName, )
		
		# Root namespaces that we can handle
		
		print "qual name:",qualifiedName
		# See if we can match the base name
		base = qualifiedName[0]
		print "trying to find",base
		if self.namespaces.has_key( base ):
			try:
				# We could just say 'return xmlFunc()', or
				# 'return self.namespaces[base].call( ... )'
				# but this way we can profile XMLRPC
				# handlers if we want.

				# The reason this is here is that XMLRPC
				# calls seemed to be going extremely slowly
				# a while ago and it was suspected that the
				# scripts weren't very quick.  Actually it
				# was the XML parser -- but I haven't taken
				# this code here out because someone might
				# want to profile scripts in future.

				import profile
				import __main__
				__main__.xmlFunc = lambda theBase=base, namespaces=self.namespaces, qualifiedName=qualifiedName, params=params: namespaces[theBase].call( qualifiedName[1:], params )
				exec 'import __main__; __main__.xmlFuncRet = __main__.xmlFunc()'
				return __main__.xmlFuncRet
			except:
				print "--- EXCEPTION %s: %s ---" % sys.exc_info()[:2]
				import traceback
				traceback.print_exc()
				raise
		
		# Couldn't match method
		raise "Namespace '%s' not found" % ( base, )






	
	
	
	
	
	
