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

def encodeUnicode( text, encoding='iso-8859-1' ):
	if type(text) == type(u''):
		text = text.encode( encoding )
	return text

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
			'requestNotification': self.requestNotification,
			'ping': self.ping,
			'mirrorPosts': self.mirrorPosts,
			}
		
		if len( method ) == 0:
			raise Exception("xmlStorageSystem method not specified")
		
		base = method[0]
		if handlers.has_key( base ):
			try:
				return handlers[base]( method[1:], params )
			except pycs_settings.PasswordIncorrect:
				return { 'flError': xmlrpclib.True,
					'message': _("Password incorrect"),
				}
			except pycs_settings.NoSuchUser:
				return { 'flError': xmlrpclib.True,
					'message': _("User not found"),
				}
		
		raise Exception("xmlStorageSystem method '%s' not found" % ( method, ))



	def registerUser( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
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
			msg = _('Welcome back, %s!') % (u.name,)
		except pycs_settings.NoSuchUser:
			u = self.set.NewUser( email, password, name )
			msg = _('Good to have you here, %s!') % (u.name)
		
		return {
			'usernum': u.usernum,
			'flError': xmlrpclib.False,
			'message': msg
			}



	def saveMultipleFiles( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, names, files = params
		print "email", email
		print "password", password
		
		u = self.set.FindUser( email, password )
		
		urlList = []
		nFilesSaved = 0
		nBytesSaved = 0
		failure = None
		for f in map( None, names, files ):
			name, file = f
			print "-> name", name #, "file", file
			
			try:
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
					raise Exception("Unknown filetype: %s" % (type(file),))
				
				# Return code
				urlList.append( "%s%s" % ( self.userFolder( email ), safeName ) )
				nFilesSaved += 1
			except Exception, e:
				import traceback
				traceback.print_exc()
				urlList.append( '' )
				if failure is None:
					failure = str(e)
				else:
					failure += '; ' + str(e)
		
		print "resulting urls:",urlList
		
		u.upstreams += nFilesSaved
		u.bytesupstreamed += nBytesSaved
		u.lastupstream = self.set.GetTime()
		self.set.Commit()

		# update 'updates' page
		self.set.AddUpdate( email )
		
		if failure is None:
			message = _('%d files have been saved for you, %s') % (nFilesSaved, u.name)
		else:
			message = failure
		
		return {
			'yourUpstreamFolderUrl': self.userFolder( email ),
			'flError': xmlrpclib.Boolean(failure),
			'message': message,
			'urlList': urlList,
			}



	def deleteMultipleFiles( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, relativepathList = params
		print "email", email
		print "password", password

		u = self.set.FindUser( email, password )
		
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
					print "--- EXCEPTION IN xmlStorageSystem.deleteMultipleFiles ---"
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
			'message': _('%d files have been deleted for you, %s') % (nFilesDeleted, u.name),
			}



	def getServerCapabilities( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password = params
		print "email", email
		print "password", password

		u = self.set.FindUser( email, password )

		search_inf = []; flHasSearch = 0; urlSearch = ''
		search_idx = self.set.mirrored_posts.find(usernum=u.usernum)
		if search_idx != -1:
			search_inf = self.set.mirrored_posts[search_idx].posts
		if len(search_inf):
			# the rationale here is to turn on flHasSearch if the search
			# feature is active for this particular user.  clients should
			# test for flCanMirrorPosts and send in a copy of their posts
			# if it exists and is true.  then, if flHasSearch becomes true,
			# put a search box on their pages ...
			flHasSearch = 1
			urlSearch = '%s/system/search.py?u=%s' % (self.set.ServerUrl(), u.usernum)
		
		return {
			'community': {
				'flCanHostComments': xmlrpclib.True,
				'flCanHostTrackback': xmlrpclib.True,
				'flCanHostAccessRestrictions': xmlrpclib.True,
				'flCanMirrorPosts': xmlrpclib.True,
				'name': self.set.LongTitle(),
				'discussionGroupUrl': 'http://radio.userland.com/discuss/',
				'domainName': self.set.ServerUrl(),
				'flHasSearch': xmlrpclib.Boolean(flHasSearch),
				'flPublic': xmlrpclib.False,
				'mailListUrl': 'http://groups.yahoo.com/group/radio-userland/',
				'urlSearch': urlSearch,
				},
			'yourUpstreamFolderUrl': self.userFolder( email ),	# user URL
			'message': _('Hello, %s, from the Python Community Server!') % (u.name,),
			'ctBytesInUse': self.userSpaceUsed( email ),
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
		if method != []: raise Exception("Namespace not found")
		
		email, password = params
		print "email", email
		print "password", password

		u = self.set.FindUser( email, password )
		
		raise NotImplementedError
		
		return {
			'flError': xmlrpclib.True,
			'message': 'Not implemented - sorry, %s!' % (u.name,),
			}



	def mailPasswordToUser( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, = params
		print "email", email

		raise NotImplementedError



	def pleaseNotify( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		notifyProcedure, port, path, protocol, urlList = params
		print "notifyProcedure", notifyProcedure
		print "port", port
		print "path", path
		print "protocol", protocol
		print "urlList", urlList
		
		raise NotImplementedError


	def requestNotification( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		notifyProcedure, port, path, protocol, urlList, userInfo = params
		print "notifyProcedure", notifyProcedure
		print "port", port
		print "path", path
		print "protocol", protocol
		print "urlList", urlList
		print "userInfo", userInfo
		
		raise NotImplementedError


	def ping( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, status, clientPort, userinfo = params
		print "email", email
		print "password", password
		print "status", status
		print "clientPort", clientPort
		print "userinfo", userinfo

		u = self.set.FindUser( email, password )
		print "---USER INFO---",userinfo,"------"

		try:
			clientPort = int(clientPort)
		except:
			pass
		u.clientPort = clientPort
		if userinfo != {}:
			u.email = userinfo['email']
			u.weblogTitle = encodeUnicode(userinfo['weblogTitle'], self.set.DocumentEncoding())
			u.serialNumber = userinfo['serialNumber']
			u.organization = encodeUnicode(userinfo['organization'], self.set.DocumentEncoding())
			u.flBehindFirewall = (userinfo['flBehindFirewall'] == xmlrpclib.True)
			u.name = encodeUnicode(userinfo['name'], self.set.DocumentEncoding())
		
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


	def mirrorPosts( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, posts = params
		print "email", email
		print "password", password
		print "%d posts to mirror" % len(posts)
		assert type(posts) == type([])

		# make sure the user exists
		self.set.FindUser( email, password )

		# make sure the user has a spot in the post mirror database
		pos = self.set.mirrored_posts.find(usernum=email)
		if pos == -1:
			self.set.mirrored_posts.append(usernum=email, posts=[])
		posts_t = self.set.mirrored_posts[pos].posts

		updateCount = 0
		addCount = 0
		# now walk through all the posts and put them in the table
		for post in posts:
			# make sure it's a dict of strings
			assert type(post) == type({})
			store_post = {}
			for k in ('date',):
				assert isinstance(post[k], xmlrpclib.DateTime)
				post[k] = post[k].value
			for k in ('date', 'postid', 'guid', 'url', 'title', 'description'):
				assert type(post[k]) in (type(''), type(u'')), "Invalid type for parameter '%s': must be some sort of string" % k
				store_post[k] = post[k].encode('utf-8')
			# if we already have this post, remove it
			postid = store_post['postid']
			assert(type(postid)==type(''))
			pos = posts_t.find(postid=postid)
			if pos != -1:
				updateCount += 1
				posts_t.delete(pos)
			else:
				addCount += 1
			# now add it
			posts_t.append(store_post)
		# all there - save
		self.set.Commit()
		# and tell the user it worked
		return {'flError': xmlrpclib.False,
			'message': '%d posts updated and %d posts added to the database for you (usernum %s).  Now you have %d posts' % (updateCount, addCount, email, len(posts_t)),
			'totalPostsKnown': len(posts_t),
			'postsMirroredNow': len(posts),
			'addedPosts': addCount,
			'updatedPosts': updateCount,
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
			name = int(name)
			
		# Now turn the number into a zero-padded string
		if type(name) == type(123):
			name = '%07d' % (name,)
			
		# Fail if it's something we don't understand now
		if type(name) != type(''):
			raise Exception("Usernum must be a string or a number")
		return self.munge( name )



	def munge( self, name ):
		# Make sure we don't have any '..'s
		if name.find( '..' ) != -1:
			raise Exception("Security warning: '..' found in filename")

		# Get rid of odd chars		
		safeName = ""
		r = re.compile( '[A-Za-z0-9\_\-\.\/]' )
		for c in name:
			if r.search( c ):
				safeName += c
			else:
				safeName += "@%02X" % (ord(c),)

		return safeName
