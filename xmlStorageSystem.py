#!/usr/bin/python

# Python Community Server
#
#     xmlStorageSystem.py: XML-RPC handler for xmlStorageSystem.*
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


"""xmlStorageSystem XML-RPC Handler

This file handles XML-RPC requests for the xmlStorageSystem namespace.

"""

import os
import sys
import re
import string
import stat

import pycs_settings
import pycs_paths

import xmlrpclib

# count used bytes in a path
def counterCallback( sumf, dir, files):
	for f in files:
		fn = os.path.join(dir, f)
		sumf[0] += os.stat(fn)[stat.ST_SIZE]

def usedBytes( path ):
	sumf = [0]
	os.path.walk( path, counterCallback, sumf )
	return sumf[0]

class xmlStorageSystem_handler:
	
	"xmlStorageSystem XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		
		
		
	def call( self, method, params ):
		print "XSS method",method #,"params",params
		
		handlers = {
			'registerUser': self.registerUser,
			'saveMultipleFiles': self.saveMultipleFiles,
			'deleteMultipleFiles': self.deleteMultipleFiles,
			'getServerCapabilities': self.getServerCapabilities,
			'getMyDirectory': self.getMyDirectory,
			'mailPasswordToUser': self.mailPasswordToUser,
			'pleaseNotify': self.pleaseNotify,
			'ping': self.ping,
			}
		
		if len( method ) == 0:
			raise "xmlStorageSystem method not specified"
		
		base = method[0]
		if handlers.has_key( base ):
			return handlers[base]( method[1:], params )
		
		raise "xmlStorageSystem method '%s' not found" % ( method, )



	def registerUser( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, name, password, clientPort, userAgent = params #, serialNumber = params
		print "email", email
		print "name", name
		print "password", password
		print "port", clientPort
		print "ua", userAgent
		#print "sn", serialNumber

		# Convert email into something we can use		
		#if type(email)==type(''):
		#	usernum = string.atoi( email )
		#elif type(email)==type(123):
		#	usernum = email
		#else:
		#	raise "Invalid type for usernum: %s" % (`type(usernum)`,)

		# See if we can find the user info
		try:
			u = self.set.FindUserByEmail( email, password )
			msg = 'Welcome back, %s!' % (u.name,)
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			u = self.set.NewUser( email, password, name )
			msg = 'Good to have you here, %s!' % (u.name)
		
		return {
			'usernum': u.usernum,
			'flError': xmlrpclib.False,
			'message': msg
			}



	def saveMultipleFiles( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, password, names, files = params
		print "email", email
		print "password", password
		
		try:
			u = self.set.FindUser( email, password )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': "User not found",
			}
		
		urlList = []
		nFilesSaved = 0
		nBytesSaved = 0
		for f in map( None, names, files ):
			name, file = f
			print "-> name", name #, "file", file
			
			# Munge the name to help protect against directory traversal attacks
			safeName = self.munge( name )
			print "safe name:", safeName
			
			# Save the file
			fullName = "%s%s" % ( self.userLocalFolder( email ), safeName ) 
			
			# See if we need to create any dirs
			r = re.compile( '(.*?)\/(.*)' )
			path = ""
			leaf = fullName
			while 1:
				#print "[ mkdir: leaf",leaf,"]"
				m = r.match( leaf )
				if not m:
					break
				dirnm, leaf = m.groups()
				path += "%s/" % (dirnm,)
				#print "  [ path",path,"  leaf",leaf,"]"
				try:
					os.mkdir( path )
				except:
					pass
			
			# Actually save the file
			if type(file)==type(''):
				# text file
				print "saving text file"
				f = open( fullName, "w" )
				f.write( file )
				nBytesSaved += len( file )
				f.close()
			elif type(file)==type(xmlrpclib.Binary()):
				# xmlrpc binary object
				print "saving xmlrpc bin obj"
				f = open( fullName, "wb" )
				f.write( file.data )
				nBytesSaved += len( file.data )
				f.close()
			else:
				raise "Unknown filetype: %s" % (type(file),)
			
			# Return code
			urlList.append( "%s%s" % ( self.userFolder( email ), safeName ) )
			nFilesSaved += 1
		
		print "resulting urls:",urlList
		
		u.upstreams += nFilesSaved
		u.bytesupstreamed += nBytesSaved
		u.lastupstream = self.set.GetTime()
		self.set.Commit()

		# update 'updates' page
		self.set.AddUpdate( email )
		
		return {
			'yourUpstreamFolderUrl': self.userFolder( email ),
			'flError': xmlrpclib.False,
			'message': '%d files have been saved for you, %s' % (nFilesSaved, u.name),
			'urlList': urlList,
			}



	def deleteMultipleFiles( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, password, relativepathList = params
		print "email", email
		print "password", password

		try:
			u = self.set.FindUser( email, password )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': "User not found",
			}
		
		flError = xmlrpclib.False
		errorList = []
		nFilesDeleted = 0
		for name in relativepathList:
			print "-> delete",name
			
			# Munge the name to help protect against directory traversal attacks
			safeName = self.munge( name )
			print "safe name:", safeName
			
			# Save the file
			fullName = "%s%s" % ( self.userLocalFolder( email ), safeName ) 
			print "full name:", fullName
			
			try:
				# FIXME: security check; have we done all we can to ensure this is safe?
				os.remove( fullName )
				errorList.append( "" )
				nFilesDeleted += 1
			except:
				flError = xmlrpclib.True
				try:
					# Dump to console
					print "--- EXCEPTION ---"
					exception, detail, traceback = sys.exc_info()
					sys.excepthook( exception, detail, traceback )
					# Send error back to client
					errorList.append( '%s: %s' % (exception, detail) )
				finally:
					del exception
					del detail
					del traceback
		
		u.deletes += nFilesDeleted
		u.lastdelete = self.set.GetTime()
		self.set.Commit()
		
		return {
			'errorList': errorList,
			'flError': flError,
			'message': '%d files have been deleted for you, %s' % (nFilesDeleted, u.name),
			}



	def getServerCapabilities( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, password = params
		print "email", email
		print "password", password

		try:
			u = self.set.FindUser( email, password )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': "User not found",
			}
		
		return {
			'community': {
				'flCanHostComments': xmlrpclib.True,
				'name': 'Python Community Server',
				'discussionGroupUrl': 'http://radio.userland.com/discuss/',
				'domainName': self.set.ServerUrl(),
				'flHasSearch': xmlrpclib.False,
				'flPublic': xmlrpclib.False,
				'mailListUrl': 'http://groups.yahoo.com/group/radio-userland/',
				'urlSearch': '',
				},
			'yourUpstreamFolderUrl': self.userFolder( email ),	# user URL
			'message': 'Hello, %s, from the Python Community Server!' % (u.name,),
			'ctBytesInUse': 0,	# bytes in use by current user FIXME
			'maxBytesPerUser': 20 * 1024*1024,	# max 20M per user
			'weblogUpdates': {
				'server': self.set.ServerHostname(),
				'port': 80,
				'protocol': 'xml-rpc',
				'rpcPath': '/RPC2',
				},
			'maxFileSize': 100 * 1024,	# max 100k per file
			'legalFileExtensions': [
				'css', 'htm', 'html', 'opml', 'text', 'rss', 'txt', 'svg', 'xml', 'root', 
				'pdf', 'doc', 'xls', 'ppt', 
				'ftsc', 'fttb', 
				'gif', 'ico', 'jpeg', 'jpg', 'png', 
				'wav', 'swf', 'sit', 'hqx', 'gz', 'zip',
				#'htaccess',
				],
			'urlRankingsByPageReads': self.set.ServerUrl() + '/system/rankings.py',
			'urlReferers': self.set.ServerUrl() + '/system/referers.py?usernum=',
			'urlSpamFreeMailto': self.set.ServerUrl() + '/system/mailto.py',
			'urlWeblogUpdates': self.set.ServerUrl() + '/system/weblogUpdates.py',
			'webBugUrl': self.set.ServerUrl() + '/system/count.py',
			'flError': xmlrpclib.False,
			}



	def getMyDirectory( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, password = params
		print "email", email
		print "password", password

		try:
			u = self.set.FindUser( email, password )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': "User not found",
			}
		
		raise "Not implemented"
		
		return {
			'flError': xmlrpclib.True,
			'message': 'Not implemented - sorry, %s!' % (u.name,),
			}



	def mailPasswordToUser( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, = params
		print "email", email

		raise "Not implemented"



	def pleaseNotify( self, method, params ):
		if method != []: raise "Namespace not found"
		
		notifyProcedure, port, path, protocol, urlList = params
		print "notifyProcedure", notifyProcedure
		print "port", port
		print "path", path
		print "protocol", protocol
		print "urlList", urlList
		
		raise "Not implemented"



	def ping( self, method, params ):
		if method != []: raise "Namespace not found"
		
		email, password, status, clientPort, userinfo = params
		print "email", email
		print "password", password
		print "status", status
		print "clientPort", clientPort
		print "userinfo", userinfo

		try:
			u = self.set.FindUser( email, password )
			
			print "---USER INFO---",userinfo,"------"

			try:
				clientPort = int(clientPort)
			except:
				pass
			u.clientPort = clientPort
			if userinfo != {}:
				u.email = userinfo['email']
				u.weblogTitle = userinfo['weblogTitle']
				u.serialNumber = userinfo['serialNumber']
				u.organization = userinfo['organization']
				u.flBehindFirewall = (userinfo['flBehindFirewall'] == xmlrpclib.True)
				u.name = userinfo['name']
			
			now = self.set.GetTime()
			
			if u.signedon:
				if status:
					# user is disconnecting
					u.signedon = 0
					u.lastsignoff = now
					u.signons += 1
			else:
				if not status:
					# user is signing on
					u.signedon = 1
					u.lastsignon = now
				
			u.lastping = now
			u.pings += 1
			if u.membersince == '':
				u.membersince = now
			
			self.set.Commit()
			
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': "Password incorrect",
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': "User not found",
			}
		

		return {
			'flError': xmlrpclib.False,
			'cloudData': {
				'email': u.email,
				'name': u.name,
				'organization': u.organization,
				'ctFileDeletions': u.deletes,
				'whenCreated': u.membersince,
				'ctAccesses': u.pings,
				'serialNumber': u.serialNumber,
				'url': self.userFolder( u.usernum ),
				'flBehindFirewall': xmlrpclib.boolean( u.flBehindFirewall ),
				'weblogTitle': u.weblogTitle,
				'ctUpstreams': u.upstreams,
				'ctSignons': u.signons,
				'whenLastAccess': u.lastping,
				'whenLastUpstream': u.lastupstream,
				'port': u.clientPort,
				'ctBytesUpstreamed': u.bytesupstreamed,
				'userAgent': "don't know",
				'ctBytesInUse': self.userSpaceUsed( u.usernum ),
				'whenLastSignOff': u.lastsignoff,
				'messageOfTheDay': '',
				'whenLastSignOn': u.lastsignon,
				'flSignedOn': xmlrpclib.boolean( u.signedon ),
				'usernum': u.usernum,
				'ip': "don't know",
			}, 
			'message': 'Pong!',
			'yourUpstreamFolderUrl': self.userFolder( email ),
		}






	# Support functions



	def userSpaceUsed( self, email ):
		return usedBytes( self.userLocalFolder( email ) )


	def userLocalFolder( self, email ):
		safeEmail = self.usernumMunge( email )
		return pycs_paths.WEBDIR + "/users/%s/" % (safeEmail,)



	def userFolder( self, email ):
		return self.set.UserFolder( email )



	def usernumMunge( self, name ):
		# We have to zero pad everything properly, so this is a bit
		# more work that normal filename munging (see below)
		
		# If we've been given a string, turn it into a number
		if type(name) == type(''):
			name = string.atoi( name )
			
		# Now turn the number into a zero-padded string
		if type(name) == type(123):
			name = '%07d' % (name,)
			
		# Fail if it's something we don't understand now
		if type(name) != type(''):
			raise "Usernum must be a string or a number"
		return self.munge( name )



	def munge( self, name ):
		# Make sure we don't have any '..'s
		if name.find( '..' ) != -1:
			raise "Security warning: '..' found in filename"

		# Get rid of odd chars		
		safeName = ""
		r = re.compile( '[A-Za-z0-9\_\-\.\/]' )
		for c in name:
			if r.search( c ):
				safeName += c
			else:
				safeName += "@%02X" % (ord(c),)

		return safeName
