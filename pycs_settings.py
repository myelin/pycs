#!/usr/bin/python

# Python Community Server
#
#     pycs_settings.py: Configuration & user info
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


import metakit
import time
import re
import ConfigParser
import pycs_paths


class Error:
	pass

class PasswordIncorrect(Error):
	pass

class NoSuchUser(Error):
	pass

class User:
	pass

class Settings:

	def __init__( self, quiet=0 ):
		storFn = pycs_paths.DATADIR + "/settings.dat"
		if not quiet:
			print "reading data from",storFn
		self.db = metakit.storage( storFn, 1 )

		confFn = pycs_paths.CONFDIR + "/pycs.conf"
		try:
			import os
			os.stat( confFn )
		except:
			raise "Can't read config data file: " + confFn
		cp = ConfigParser.ConfigParser()
		cp.read( confFn )

		# Read in general config		
		self.conf = self.readAllOptions( cp, "main" )
		
		defaults = cp.defaults()
		for v in self.conf.keys():
			defaults[v] = self.conf[v]
		
		# Read in name aliases
		self.aliases = self.readAllOptions( cp, "aliases" )
		
		# Strip extra slashes off the name aliases
		for user in self.aliases.keys():
			alias = self.aliases[user]
			if len( alias ) and alias[-1] == '/':
				self.aliases[user] = alias[:-1]		

		# User info - one row per user
		self.users = self.db.getas(
			"users[usernum:S,email:S,password:S,name:S,weblogTitle:S,serialNumber:S,organization:S," +
			"flBehindFirewall:I,hitstoday:I,hitsyesterday:I,hitsalltime:I," +
			"membersince:S,lastping:S,pings:I,lastupstream:S,upstreams:I,lastdelete:S,deletes:I," +
			"signons:I,signedon:I,lastsignon:S,lastsignoff:S,clientPort:I]"
			).ordered()
			
		if len(self.users) == 0:
			# Blank database - put any predefined users here
			pass

		# Metadata - only one row
		self.meta = self.db.getas( "meta[nextUsernum:I]" )
		if len(self.meta) == 0:
			# initialize row
			self.meta.append( nextUsernum=1 )
			self.Commit()
			
		# Update data
		self.updates = self.db.getas( "updates[time:S,usernum:S,title:S]" ).ordered(2)

		# Referrer data
		self.referrers = self.db.getas( "referrers[time:S,usernum:S,group:S,referrer:S,count:I]" ).ordered(2)
		
		if not quiet:
			self.DumpData()

	def readAllOptions( self, cp, section ):
		conf = {}
		for opt in cp.options( section ):
			conf[opt] = cp.get( section, opt )
		return conf

	def ServerUrl( self ):
		return self.conf['serverurl']

	def ServerHostname( self ):
		return self.conf['serverhostname']

	def ServerPort( self ):
		return int( self.conf['serverport'] )

	def GetDate( self ):
		(y, m, d, hh, mm, ss, wday, jday, dst) = time.localtime()
		
		return '%04d-%02d-%02d' % (y, m, d)

	def GetTime( self ):
		(y, m, d, hh, mm, ss, wday, jday, dst) = time.localtime()
		
		# Time of day
		pm = 'AM'
		if hh > 11: pm = 'PM'
		if hh == 0: hh = 12
		elif hh > 12: hh -= 12
		
		return '%04d-%02d-%02d %02d:%02d:%02d %s' % (y, m, d, hh, mm, ss, pm)

	def AddUpdate( self, usernum ):
		theTime = self.GetTime()
		
		user = self.User( usernum )
		logTitle = user.weblogTitle
		
		# See if that user has updated today already
		sth = self.updates.select( { 'usernum': usernum } )
		row = None
		if len( sth ) != 0:
			# They have - update the timestamp
			row = sth[0]
			row.time = theTime
			row.title = logTitle
		else:
			# They haven't - add a new row to the DB
			self.updates.append( {
				'usernum': usernum,
				'time': theTime,
				'title': logTitle,
				} )
			
		self.Commit()

	def AddReferrer( self, usernum, group, referrer ):
		theTime = self.GetTime()

		# add some regexps to ignore when adding Referrers
		# this should actually be pulled out of the config, I think
		userfolder = self.UserFolder( usernum )
		ignoreReferrers = [
			re.compile( '^' + userfolder ),
			re.compile( r'^http://127\.0\.0\.1:\d+/' ),
			re.compile( r'^http://localhost:\d+/' ),
			]
		if userfolder[-1:] == '/':
			ignoreReferrers.append(
			re.compile('^'+ userfolder[:-1] +'$'))

		# check for URLs to ignore as referrer
		ignoreit = 0
		for url in ignoreReferrers:
			if url.match(referrer):
				ignoreit = 1

		# we got something that shouldn't be ignored
		if not(ignoreit):
			# See if that user+group+referrer combination
			# is already there
			sth = self.referrers.select( {
				'usernum': usernum,
				'group': group,
				'referrer': referrer
				} )
			if len( sth ) != 0:
				# it is, so update the timestamp and count
				row = sth[0]
				row.time = theTime
				row.count += 1
			else:
				# it isn't, so add a new row to the DB
				self.referrers.append( {
					'usernum': usernum,
					'time': theTime,
					'group': group,
					'referrer': referrer,
					'count': 1
					} )
			self.Commit()
			
	def Commit( self ):
		self.db.commit()
		
	def DumpData( self ):
		self.DumpMeta()
		self.DumpUsers()
		
	def DumpMeta( self ):
		print "Dumping metadata"
		meta = self.meta[0]
		st = self.meta.structure()
		for col in st:
			print "  %s: %s" % ( col.name, getattr( meta, col.name ) )
	
	def DumpUsers( self ):
		print "Dumping user data"
		st = self.users.structure()
		for u in self.users:
			print "USER"
			for col in st:
				print "  %s: %s" % ( col.name, getattr( u, col.name ) )

	def FormatUsernum( self, usernum ):
		
		"Converts a usernum into DB-format, e.g. 123 -> '0000123'"
		
		if type(usernum)==type(''):
			# zero-pad it
			return ( '0' * ( 7 - len(usernum) ) ) + usernum
		else:
			# convert to a string
			return "%07d" % (usernum,)
	
	def User( self, usernum ):
	
		"See if the user exists, and return its DB row if it does"

		no = self.FormatUsernum( usernum )
		
		row = self.users.select( { 'usernum': self.FormatUsernum( no ) } )
		
		if len(row) == 0:
			print "User not found (%s)!" % (no,)
			raise NoSuchUser
			
		return row[0]

	def FindUser( self, usernum, password ):
	
		"Find a user and verify the password"
		
		u = self.User( usernum )
		
		if u.password != password:
			print "Password incorrect (for %s) !" % (usernum,)
			raise PasswordIncorrect
		return u

	def FindUserByEmail( self, email, password):
		# Look for user with that address
		vw = self.users.select( { 'email': email } )
		
		# If we got a blank view, the user doesn't exist
		if len(vw) == 0:
			raise NoSuchUser
		
		# Get the user row (there should only be one)
		u = vw[0]
		
		if u.password != password:
			raise PasswordIncorrect
			
		return u
		

	def NewUser( self, email, password, name ):
		# Prepare new row
		user = User()

		# Make sure we're not full already
		if self.conf.has_key( 'maxusernum' ):
			if int( self.meta[0].nextUserNum ) >= int( self.conf['maxusernum'] ):
				raise "Sorry; we're full!  We can't take any more users"
		
		while 1:
			# Assign a usernum and keep incrementing until we get
			# an unused one.  Will only need to increment if the
			# user table has been manually edited.
			
			user.usernum = "%07d" % (self.meta[0].nextUsernum,)
			self.meta[0].nextUsernum += 1
			
			if len( self.users.select( { 'usernum': user.usernum } ) ) == 0:
				# We have a unique usernum - stop looking
				break
		
		user.email = email
		user.password = password
		user.name = name

		# Increment max usernum and add row to users
		print "New user row =",self.users.append( user.__dict__ )
		self.Commit()

		return user

	def UserFolder( self, usernum ):
		formattedUsernum = self.FormatUsernum( usernum )
		#print "find user folder: usernum =", usernum, " formatted usernum =",formattedUsernum
		if self.aliases.has_key( formattedUsernum ):
			#print "got alias for this:", self.aliases[formattedUsernum]
			return self.aliases[formattedUsernum] + '/'
		else:
			#print "no alias"
			return self.ServerUrl() + "/users/%s/" % ( formattedUsernum, )
		
	# Template renderer
	def Render( self, data ):
		# Renders 'data' into html
		# data = {
		#	'title': page title,
		#	'body': body text,
		#	}
		
		out = """<html>
	<head>
		<title>Python Community Server: %s</title>
		<link rel="stylesheet" href="%s/pycs.css" type="text/css" />
	</head>
	<body>
		<h1>PyCS: <strong>%s</strong></h1>
		<div class="margins">
		%s
		</div>
	</body>
	</html>""" % ( data['title'], self.ServerUrl(),
			data['title'], data['body'] )
	
		return out

