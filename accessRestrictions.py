#!/usr/bin/python

# Python Community Server
#
#     accessRestrictions.py: XML-RPC handler for accessRestrictions.*
#
# Copyright (c) 2003, Georg Bauer <gb@murphy.bofh.ms>
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


"""accessRestrictions XML-RPC Handler

This file handles XML-RPC requests for the accessRestrictions namespace.

"""

import os
import sys
import re
import string
import stat
import md5

import pycs_settings
import pycs_paths

import xmlrpclib
import metakit

class accessRestrictions_handler:
	
	"accessRestrictions XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		self.locations = self.set.db.getas(
			"arlocations[blogid:S,locname:S,regexp:S,group[name:S]]"
		).ordered(2)
		self.groups = self.set.db.getas(
			"argroups[blogid:S,name:S,user[name:S]"
		).ordered(2)
		self.users = self.set.db.getas(
			"arusers[blogid:S,name:S,password:S]"
		).ordered(2)
		
	def checkUrlAccess( self, usernum, url, user, password, quiet=0 ):
		if not(quiet): print "checking URL %s for user %s" % ( url, user )
		if user:
			password = md5.md5(password).hexdigest()
			ures = self.users.select({'blogid':usernum, 'name':user})
			if len(ures) == 0:
				if not(quiet): print "user %s not defined" % user
				return 0
			if str(ures[0].password) != password:
				if not(quiet): print "password for user %s wrong" % user
				return 0
		elif password:
			if not(quiet): print "password for anonymous user given"
			return 0
		matched = 0
		for location in self.locations.select({'blogid':usernum}):
			if re.match(location.regexp, url):
				matched = 1
				for group in location.group:
					for grec in self.groups.select({'blogid':usernum, 'name':group.name}):
						for urec in grec.user:
							if urec.name == user:
								if not(quiet): print "user %s valid for location %s" % (user, location.locname)
								return 1
		return not(matched)
		
	def call( self, method, params ):
		print "AR method",method #,"params",params
		
		handlers = {
			'setUser': self.setUser,
			'delUser': self.delUser,
			'getUserList': self.getUserList,
			'setGroup': self.setGroup,
			'addUserToGroup': self.addUserToGroup,
			'delUserFromGroup': self.delUserFromGroup,
			'getUserListForGroup': self.getUserListForGroup,
			'delGroup': self.delGroup,
			'getGroupList': self.getGroupList,
			'setLocation': self.setLocation,
			'addGroupToLocation': self.addGroupToLocation,
			'delGroupFromLocation': self.delGroupFromLocation,
			'getGroupListForLocation': self.getGroupListForLocation,
			'getUserListForLocation': self.getUserListForLocation,
			'delLocation': self.delLocation,
			'getLocationList': self.getLocationList,
			}
		
		if len( method ) == 0:
			raise Exception("accessRestrictions method not specified")
		
		base = method[0]
		if handlers.has_key( base ):
			return handlers[base]( method[1:], params )
		
		raise Exception("accessRestrictions method '%s' not found" % ( method, ))



	def setUser( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, username, password = params
		password = md5.md5(password).hexdigest()
		print "blogid", blogid
		print "username", username
		print "password", password

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		res = self.users.select({'blogid':u.usernum, 'name':username})
		if len(res):
			res[0].password = password
		else:
			self.users.append({
				'blogid': u.usernum,
				'name': username,
				'password': password,
			})
		self.set.Commit()
		
		return {
			'flError': xmlrpclib.False,
			'message': _("user %s added" % username)
			}
		
	def delUser( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, username = params
		print "blogid", blogid
		print "username", username

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		(idx, found) = self.users.locate({'blogid':u.usernum,'name':username})
		if found:
			for group in self.groups.select({'blogid':u.usernum}):
				ures = group.user.select({'name':username})
				if len(ures):
					return { 'flError': xmlrpclib.True,
						'message': _("user %s is in group %s" % (username, group.name))
					}
			self.users.delete(idx)
			self.set.Commit()
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("user %s not found" % username),
			}

		return {
			'flError': xmlrpclib.False,
			'message': _("user %s deleted" % username)
			}
		
	def getUserList( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw = params
		print "blogid", blogid

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		userlist = []
		for user in self.users.select({'blogid':u.usernum}):
			userlist.append({
				'name':user.name,
			})

		return {
			'userlist': userlist,
			'flError': xmlrpclib.False,
			'message': _("userlist returned")
			}
		
	def setGroup( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, groupname = params
		print "blogid", blogid
		print "groupname", groupname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res) == 0:
			self.groups.append({
				'blogid': u.usernum,
				'name': groupname,
				'user': metakit.view()
			})
			self.set.Commit()
		
		return {
			'flError': xmlrpclib.False,
			'message': _("group %s added" % groupname)
			}
		
	def addUserToGroup( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, groupname, username = params
		print "blogid", blogid
		print "groupname", groupname
		print "username", username

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		res = self.users.select({'blogid':u.usernum, 'name':username})
		if len(res) == 0:
			return {
				'flError': xmlrpclib.True,
				'message': _("user %s not found" % username)
				}

		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res):
			ures = res[0].user.select({'name':username})
			if len(ures) == 0:
				res[0].user.append({'name': username})
				self.set.Commit()
				return {
					'flError': xmlrpclib.False,
					'message': _("user %s added to group %s" % (username, groupname))
					}
			else:
				return {
					'flError': xmlrpclib.True,
					'message': _("user %s already in group %s" % (username, groupname))
					}
		else:
			return {
				'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname)
				}
		
	def delUserFromGroup( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, groupname, username = params
		print "blogid", blogid
		print "groupname", groupname
		print "username", username

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.users.select({'blogid':u.usernum, 'name':username})
		if len(res) == 0:
			return {
				'flError': xmlrpclib.True,
				'message': _("user %s not found" % username)
				}

		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res):
			idx = res[0].user.find({'name':username})
			if idx >= 0:
				res[0].user.delete(idx)
				self.set.Commit()
				return {
					'flError': xmlrpclib.False,
					'message': _("user %s deleted from group %s" % (username, groupname))
					}
			else:
				return {
					'flError': xmlrpclib.True,
					'message': _("user %s not found in groupo %s" % (username, groupname))
					}
		else:
			return {
				'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname)
				}
		
	def getUserListForGroup( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, groupname = params
		print "blogid", blogid
		print "groupname", groupname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res):
			userlist = []
			for user in res[0].user:
				userlist.append({
					'name':user.name,
				})
			return { 'flError': xmlrpclib.False,
				'message': _("userlist for group %s returned" % groupname),
				'userlist': userlist,
			}
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname),
			}

		
	def delGroup( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, groupname = params
		print "blogid", blogid
		print "groupname", groupname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}

		(idx, found) = self.groups.locate({'blogid':u.usernum,'name':groupname})
		if found:
			for location in self.locations.select({'blogid':u.usernum}):
				ures = location.group.select({'name':groupname})
				if len(ures):
					return { 'flError': xmlrpclib.True,
						'message': _("group %s is in location %s" % (groupname, location.locname))
					}
			self.groups.delete(idx)
			self.set.Commit()
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname),
			}

		return {
			'flError': xmlrpclib.False,
			'message': _("group %s deleted" % groupname)
			}
		
	def getGroupList( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw = params
		print "blogid", blogid

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		grouplist = []
		for group in self.groups.select({'blogid':u.usernum}):
			userlist = []
			for user in group.user:
				userlist.append({
					'name':user.name,
				})
			grouplist.append({
				'name':group.name,
				'userlist':userlist,
			})

		return {
			'grouplist': grouplist,
			'flError': xmlrpclib.False,
			'message': _("grouplist returned")
			}
		
	def setLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname, regexp = params
		print "blogid", blogid
		print "locname", locname
		print "regexp", regexp

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.locations.select({'blogid':u.usernum, 'locname':locname})
		if len(res):
			res[0].regexp = regexp
		else:
			self.locations.append({
				'blogid': u.usernum,
				'locname': locname,
				'regexp': regexp,
				'group': metakit.view()
			})
		self.set.Commit()
		
		return {
			'flError': xmlrpclib.False,
			'message': _("location %s added" % locname)
			}
		
	def addGroupToLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname, groupname = params
		print "blogid", blogid
		print "locname", locname
		print "groupname", groupname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res) == 0:
			return {
				'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname)
				}

		res = self.locations.select({'blogid':u.usernum, 'locname':locname})
		if len(res):
			gres = res[0].group.select({'name':groupname})
			if len(gres) == 0:
				res[0].group.append({'name': groupname})
				self.set.Commit()
				return {
					'flError': xmlrpclib.False,
					'message': _("group %s added to location %s" % (groupname, locname))
					}
			else:
				return {
					'flError': xmlrpclib.True,
					'message': _("group %s already in location %s" % (groupname, locname))
					}
		else:
			return {
				'flError': xmlrpclib.True,
				'message': _("location %s not found" % locname)
				}
		
	def delGroupFromLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname, groupname = params
		print "blogid", blogid
		print "locname", locname
		print "groupname", groupname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.groups.select({'blogid':u.usernum, 'name':groupname})
		if len(res) == 0:
			return {
				'flError': xmlrpclib.True,
				'message': _("group %s not found" % groupname)
				}

		res = self.locations.select({'blogid':u.usernum, 'locname':locname})
		if len(res):
			idx = res[0].group.find({'name':groupname})
			if idx >= 0:
				res[0].group.delete(idx)
				self.set.Commit()
				return {
					'flError': xmlrpclib.False,
					'message': _("group %s deleted from location %s" % (groupname, locname))
					}
			else:
				return {
					'flError': xmlrpclib.True,
					'message': _("group %s not found in location %s" % (groupname, locname))
					}
		else:
			return {
				'flError': xmlrpclib.True,
				'message': _("location %s not found" % locname)
				}
		
	def getGroupListForLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname = params
		print "blogid", blogid
		print "locname", locname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.locations.select({'blogid':u.usernum, 'locname':locname})
		if len(res):
			grouplist = []
			for group in res[0].group:
				gres = self.groups.select({'blogid':blogid,'name':group.name})
				userlist = []
				for user in gres[0].user:
					userlist.append({
						'name':user.name
					})
				grouplist.append({
					'name':group.name,
					'userlist':userlist,
				})
			return { 'flError': xmlrpclib.False,
				'message': _("grouplist for location %s returned" % locname),
				'grouplist': grouplist,
			}
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("location %s not found" % locname),
			}
		
	def getUserListForLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname = params
		print "blogid", blogid
		print "locname", locname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		res = self.locations.select({'blogid':u.usernum, 'locname':locname})
		if len(res):
			userlist = []
			userhash = {}
			for group in res[0].group:
				gres = self.groups.select({'blogid':u.usernum, 'name':group.name})
				for grec in gres:
					for user in grec.user:
						if not(userhash.has_key(user.name)):
							userlist.append({
								'name':user.name
							})
			return { 'flError': xmlrpclib.False,
				'message': _("userlist for location %s returned" % locname),
				'userlist': userlist,
			}
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("location %s not found" % locname),
			}

	def delLocation( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw, locname = params
		print "blogid", blogid
		print "locname", locname

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		(idx, found) = self.locations.locate({'blogid':u.usernum,'locname':locname})
		if found:
			self.locations.delete(idx)
			self.set.Commit()
		else:
			return { 'flError': xmlrpclib.True,
				'message': _("location %s not found" % locname),
			}

		return {
			'flError': xmlrpclib.False,
			'message': _("location %s deleted" % locname)
			}
		
	def getLocationList( self, method, params ):
		if method != []: raise Exception("Namespace not found")
		
		blogid, blogpw = params
		print "blogid", blogid

		# See if we can find the user info
		try:
			u = self.set.FindUser( blogid, blogpw )
		except pycs_settings.PasswordIncorrect:
			return { 'flError': xmlrpclib.True,
				'message': _("Password incorrect"),
			}
		except pycs_settings.NoSuchUser:
			return { 'flError': xmlrpclib.True,
				'message': _("User not found"),
			}
		
		loclist = []
		for loc in self.locations.select({'blogid':u.usernum}):
			grouplist = []
			for group in loc.group:
				grouplist.append(group.name)
			loclist.append({
				'name':loc.locname,
				'regexp':loc.regexp,
				'grouplist':grouplist
			})

		return {
			'locationlist': loclist,
			'flError': xmlrpclib.False,
			'message': _("locationlist returned")
			}

