#!/usr/bin/python

# Python Community Server
#
#     pycs_module_handler.py: Script handler
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


"""PyCS Module Handler

This is to do the same thing as mod_perl under Apache -- when a 
request is received, see if the corresponding file exists.  If
we have a compiled copy in memory, check to make sure it hasn't
been changed since we compiled it, then run it.  If our cache
is stale or we don't have a compiled copy, compile it then run
it.

"""

import re
import sys
import os
import time
import StringIO
import pycs_http_util
import pycs_paths




class collector:

	def __init__ (self, handler, length, request):
		self.handler = handler
		self.request = request
		self.request.collector = self
		self.request.channel.set_terminator (length)
		self.buffer = StringIO.StringIO()

	def collect_incoming_data (self, data):
		self.buffer.write (data)

	def found_terminator (self):
		self.buffer.seek(0)
		self.request.collector = None
		self.request.channel.set_terminator ('\r\n\r\n')
		self.handler.continue_request (
			self.request,
			self.buffer
			)


	

class cached_module:

	def __init__( self, path ):
		self.module = None
		self.lastModified = None
		self.path = path
		
		self.Recompile()
	
	def Recompile( self ):
		"Compile module and store results in self.module"
		print "compiling %s" % (self.path,)
		code = open( self.path, 'r' ).read()
		#code = string.replace( code, "\r", "" )
		#print code
		self.module = compile(
			code,
			self.path,
			'exec'
			)
	
	def Call( self, params ):
		return eval( self.module, params )


class pycs_module_handler:

	match_regex = re.compile(
		r'^/system/'
		)

	def __init__( self, settings ):
		print "[generic module handler]"
		
		# System-wide settings (database handle etc)
		self.set = settings
		
		# Cache of compiled scripts
		self.module_cache = {}
		
		#self.db = metakit.storage( 'conf/comments.dat', 1 )
		
		# order by user & paragraph
		#self.comments = self.db.getas(
		#	'comments[user:S,paragraph:S,notes[name:S,email:S,url:S,comment:S]]'
		#	).ordered( 2 )
	
	def match( self, request ):
		[path, params, query, fragment] = request.split_uri()
		#print "attempt to match '%s'" % (path,)
		m = self.match_regex.match( path )
		return( m != None )
	
	def handle_request( self, request ):
		if request.command.lower() in ('put', 'post'):
			# look for a Content-Length header.
			cl = request.get_header ('content-length')
			length = int(cl)
			if not cl:
				request.error (411)
			else:
				collector (self, length, request)
		else:
			self.continue_request (request, StringIO.StringIO())

	def continue_request( self, request, input_data ):
		start_time = time.time()
		try:
			# try to find module
			[path, params, query, fragment] = request.split_uri()
			#print "path to module:",path
			
			realPath = pycs_paths.MODDIR + path
			if re.compile( "\.\." ).search( realPath ):
				raise "Security error: '..' found in path"
			#print "real path:",realPath
			
			try:
				st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = os.stat( realPath )
				#print "modified", f.st_mtime
				
				if self.module_cache.has_key( realPath ):
					mod = self.module_cache[realPath]
					if st_mtime != mod.lastModified:
						# We need to recompile the module
						mod.Recompile()
						mod.lastModified = st_mtime
				else:
					# We don't have it cached - compile it
					mod = cached_module( realPath )
					# Put it in the cache
					self.module_cache[realPath] = mod
					# Mark it as 'fresh'
					mod.lastModified = st_mtime
					
			except os.error:
				print "--- CAN'T FIND FILE %s ---" % (realPath,)
				request.error( 404 )
				return
			
			# call module
			ret = mod.Call( {
				'request': request,
				'input_data': input_data,
				'set': self.set,
				'util': pycs_http_util,
				} )

			print "call to %s took %.1f s" % (realPath, time.time() - start_time)
			return ret
		except SystemExit:
			raise
		except:
			# print browser error and log backtrace
			try:
				print>>sys.stderr, "--- EXCEPTION IN MODULE ---"
				exception, detail, traceback = sys.exc_info()
				sys.excepthook( exception, detail, traceback )
			finally:
				del exception
				del detail
				del traceback
			
			request.error( 500 )
			return
		
		raise "should never get here"
	
	#def continue_request( self, request ):
	#	pass
