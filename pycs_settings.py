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

	def __init__( self ):

		self.db = metakit.storage( pycs_paths.DATADIR + "/settings.dat", 1 )
		cp = ConfigParser.ConfigParser()
		cp.read( pycs_paths.CONFDIR + "/pycs.conf" )

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
			"flBehindFirewall:I]"
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
		<title>Python Community Server: """ + data['title'] + """</title>
		<style type="text/css">
		<!--
			body {
				font-family: arial, sans-serif;
				font-size: 12pt
				}
			td {
				background-color: lightyellow
				}
			td.maintitle {
				font-size: 24pt
				}
			.black {
				background-color: black
				}
		-->
		</style>
	</head>
	<body>
		<table width="100%" cellspacing="0" cellpadding="2"><tr><td class="black">
		<table width="100%" cellspacing="0" cellpadding="10"><tr><td class="maintitle">
			PyCS: <strong>""" + data['title'] + """</strong>
		</td></tr></table>
		</td></tr><table>
		"""
		out += data['body']
		out +=  """
	</body>
	</html>"""
	
		return out

