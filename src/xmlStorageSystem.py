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
import traceback

import pycs_settings
import pycs_paths

import xmlrpclib

def encodeUnicode( text, encoding='iso-8859-1' ):
	if type(text) == type(u''):
		text = text.encode( encoding )
	return text

class xmlStorageSystem_handler:
	
	"xmlStorageSystem XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		
		
		
	def call( self, method, params ):
#		print "XSS method",method #,"params",params
		
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
			'deleteMirroredPosts': self.deleteMirroredPosts,
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
			except:
				traceback.print_exc()
				raise
		
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
				safeName = self.set.Munge( name )
				print "safe name:", safeName
				
				# Save the file
				fullName = "%s%s" % ( self.set.UserLocalFolder( email ), safeName ) 
				
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
					path += "%s" % (dirnm,)
					#print "  [ path",path,"  leaf",leaf,"]"
					try:
						os.mkdir( path )
					except:
						pass
					path += "/"
				
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
		# Bytes upstreamed can wrap around on 2 GB, so prevent
		# this from happening
		try: u.bytesupstreamed += nBytesSaved
		except TypeError: u.bytesupstreamed = nBytesSaved
		u.bytesused = self.set.UserSpaceUsed(email)
		u.lastupstream = self.set.GetTime()
		u.save()

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
			safeName = self.set.Munge( name )
			print "safe name:", safeName
			
			# Save the file
			fullName = "%s%s" % ( self.set.UserLocalFolder( email ), safeName ) 
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
		u.bytesused = self.set.UserSpaceUsed(email)
		u.save()
		
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

		flHasSearch = 0; urlSearch = ''
		if self.set.pdb.fetchone("SELECT postguid FROM pycs_mirrored_posts WHERE usernum=%d LIMIT 1", (u.usernum,)):
			# return flHasSearch=true if the user has
			# mirrored at least one post into the
			# database.  clients should test for
			# flCanMirrorPosts and send in a copy of their
			# posts if it exists and is true.  then, if
			# flHasSearch becomes true, put a search box
			# on their pages.
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
			'ctBytesInUse': u.bytesused,
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
#		print "---USER INFO---",userinfo,"------"

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
		
		now = str(self.set.GetDbTime())
		
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
		if not u.membersince:
			u.membersince = now

		u.save()
			

		ret = {
			'flError': xmlrpclib.False,
			'cloudData': {
				'email': u.email,
				'name': u.name,
				'organization': u.organization,
				'ctFileDeletions': u.deletes,
				'whenCreated': u.membersince and str(u.membersince) or '',
				'ctAccesses': u.pings,
				'serialNumber': u.serialNumber,
				'url': self.userFolder( u.usernum ),
				'flBehindFirewall': xmlrpclib.boolean( u.flBehindFirewall ),
				'weblogTitle': u.weblogTitle,
				'ctUpstreams': u.upstreams,
				'ctSignons': u.signons,
				'whenLastAccess': u.lastping,
				'whenLastUpstream': u.lastupstream and str(u.lastupstream) or '',
				'port': u.clientPort,
				'ctBytesUpstreamed': u.bytesupstreamed,
				'userAgent': "don't know",
				'ctBytesInUse': u.bytesused,
				'whenLastSignOff': u.lastsignoff and str(u.lastsignoff) or '',
				'messageOfTheDay': '',
				'whenLastSignOn': u.lastsignon and str(u.lastsignon) or '',
				'flSignedOn': xmlrpclib.boolean( u.signedon ),
				'usernum': u.usernum,
				'ip': "don't know",
			}, 
			'message': 'Pong!',
			'yourUpstreamFolderUrl': self.userFolder( email ),
		}

		print "ret=",ret
		
		return ret


	def mirrorPosts( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, posts = params
		print "email", email
		print "password", password
		print "%d posts to mirror" % len(posts)
		assert type(posts) == type([])

		# make sure the user exists
		u = self.set.FindUser( email, password )

		updateCount = 0
		addCount = 0
		# now walk through all the posts and put them in the table
		for post in posts:
			# make sure it's a dict of strings
			assert type(post) == type({})
			store_post = {}
			for k in ('date',):
				assert isinstance(post[k], xmlrpclib.DateTime)
				post[k] = post[k].value.encode('utf-8')
			for k in ('date', 'postid', 'guid', 'url', 'title', 'description'):
				assert type(post[k]) in (type(''), type(u'')), "Invalid type for parameter '%s': must be some sort of string" % k
				if type(post[k]) == type(u''):
					store_post[k] = post[k].encode('utf-8')
				else:
					store_post[k] = post[k]
			# if we already have this post, remove it
			postid = store_post['postid']
			assert(type(postid)==type(''))
			self.set.pdb.execute("DELETE FROM pycs_mirrored_posts WHERE usernum=%d AND postid=%s",
					     (u.usernum, postid))
			# now add it
			print `post['date']`
			self.set.pdb.execute("INSERT INTO pycs_mirrored_posts (usernum, postdate, postid, postguid, posturl, posttitle, postcontent) VALUES (%d, %s, %s, %s, %s, %s, %s)", (
				u.usernum,
				post['date'],
				post['postid'],
				post['guid'],
				post['url'],
				post['title'],
				post['description'],
				))
		post_count, = self.set.pdb.fetchone("SELECT COUNT(*) FROM pycs_mirrored_posts WHERE usernum=%d", (u.usernum,))
		# and tell the user it worked
		return {'flError': xmlrpclib.False,
			'message': _('%d posts updated and %d posts added to the database for you (usernum %s).  Now you have %d posts') % (updateCount, addCount, email, post_count),
			'totalPostsKnown': post_count,
			'postsMirroredNow': len(posts),
			'addedPosts': addCount,
			'updatedPosts': updateCount,
			}

	def deleteMirroredPosts( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		email, password, postids = params
		print "email", email
		print "password", password
		print "%d posts to delete from mirror" % len(postids)
		assert type(postids) == type([])

		# make sure the user exists
		u = self.set.FindUser( email, password )

		# delete the posts
		orig_count, = self.set.pdb.fetchone("SELECT COUNT(*) FROM pycs_mirrored_posts WHERE usernum=%d", (u.usernum,))
		for postid in postids:
			self.set.pdb.execute("DELETE FROM pycs_mirrored_posts WHERE usernum=%d AND postid=%s",
					     (u.usernum, postid))
		final_count, = self.set.pdb.fetchone("SELECT COUNT(*) FROM pycs_mirrored_posts WHERE usernum=%d", (u.usernum,))

		# now tell the user it worked
		return {'flError': xmlrpclib.False,
			'message': _('%d posts deleted from the database for you (usernum %d).  Now you have %d posts') % (orig_count - final_count, u.usernum, final_count),
			'totalPostsKnown': final_count,
			'postsDeletedNow': len(postids),
			'deletedPosts': orig_count - final_count,
			}




	# Support functions

	def userFolder( self, email ):
		return self.set.UserFolder( email )



