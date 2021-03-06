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


import time
import re
import os
import stat
import os.path
import md5
import ConfigParser
import types
import pycs_paths
import pycs_db
import mx.DateTime


class Error:
	pass

class PasswordIncorrect(Error):
	pass

class NoSuchUser(Error):
	pass

class User:
	valid_columns = [
		"usernum",
		"email",
		"password",
		"name",
		"weblogTitle",
		"serialNumber",
		"organization",
		"flBehindFirewall",
		"hitstoday",
		"hitsyesterday",
		"hitsalltime",
		"membersince",
		"lastping",
		"pings",
		"lastupstream",
		"upstreams",
		"lastdelete",
		"deletes",
		"bytesupstreamed",
		"signons",
		"signedon",
		"lastsignon",
		"lastsignoff",
		"clientPort",
		"disabled",
		"alias",
		"flManila",
		"bytesused",
		"stylesheet",
		"commentsdisabled",
		]
	valid_columns_lookup = dict([(x.lower(), 1) for x in valid_columns])
	def __init__(self, set, data=None):
		if data is None: data = {}
		self.__dict__['data'] = data
		self.__dict__['changed_columns'] = {}
		self.__dict__['set'] = set
	def __getattr__(self, k):
		d = self.__dict__['data']
		k = k.lower()
		if type(d) == types.DictType:
			return d[k]
		else:
			return getattr(d, k)
	def __setattr__(self, k, v):
		k = k.lower()
		assert (User.valid_columns_lookup.has_key(k)), ("DB column %s doesn't exist" % k)
		d = self.__dict__['data']
		if type(d) == types.DictType:
			d[k] = v
		else:
			setattr(d, k, v)
		self.__dict__['changed_columns'][k] = 1
	def save(self):
#		print "saving changed columns to db:",self.__dict__['changed_columns']
		self.__dict__['set'].save_user_to_db(self)
		
# count used bytes in a path
def counterCallback( sumf, dir, files):
	for f in files:
		fn = os.path.join(dir, f)
		sumf[0] += os.stat(fn)[stat.ST_SIZE]

def usedBytes( path ):
	sumf = [0]
	os.path.walk( path, counterCallback, sumf )
	return sumf[0]

class Settings:

	def __init__(self, quiet=0, nopg=0, noupgrade=0, authorizer=None):
		self.authorizer = authorizer
		self.rewrite_h = None
		self.ar_h = None
		
		confFn = pycs_paths.CONFDIR + "/pycs.conf"
		try:
			os.stat(confFn)
		except:
			raise "Can't read config data file: " + confFn
		cp = ConfigParser.ConfigParser()
		cp.read(confFn)

		# Read in general config		
		self.conf = self.readAllOptions(cp, "main")
		
		defaults = cp.defaults()
		for v in self.conf.keys():
			defaults[v] = self.conf[v]
		
		# Read in name aliases
		self.aliases = self.readAllOptions(cp, "aliases")
		
		# Strip extra slashes off the name aliases
		for user in self.aliases.keys():
			alias = self.aliases[user]
			if len(alias) and alias[-1] == '/':
				self.aliases[user] = alias[:-1]		

		# Set up PostgreSQL connection
		if not nopg:
			if not self.conf.has_key("pg_host"):
				print "ERROR: You do not have the pg_* variables set up in pycs.conf.  Are you upgrading from a version that only used MetaKit?  Please read the documentation, and pycs.conf.default, for more information."
				raise SystemExit(0)
			self.pdb = pycs_db.DB(self, self.conf['pg_host'], self.conf['pg_db'], self.conf['pg_user'], self.conf['pg_pass'], noupgrade=noupgrade)

	def getCommentTable(self):
		if hasattr(self, 'comments'):
			return self.comments
		return None #FIXME: remove this function once we get comments all sorted out

	def readAllOptions(self, cp, section):
		conf = {}
		for opt in cp.options(section):
			conf[opt] = cp.get(section, opt)
		return conf

	def ServerUrl(self):
		return self.conf['serverurl']

	def ServerHostname(self):
		return self.conf['serverhostname']

	def ServerPort(self):
		return int(self.conf['serverport'])

	def DefaultConfigValue(self, key, value):
		if self.conf.has_key(key):
			return self.conf[key]
		else:
			return value

	def Language(self):
		return self.DefaultConfigValue('language', 'en')

	def DocumentEncoding(self):
		return self.DefaultConfigValue('documentencoding', 'iso-8859-1')

	def MailEncoding(self):
		return self.DefaultConfigValue('mailencoding', 'iso-8859-1')

	def ServerMailTo(self):
		return self.DefaultConfigValue('servermailto', 'python-community-server-mailto@myelin.co.nz')

	def LongTitle(self):
		return self.DefaultConfigValue('longtitle', 'Python Community Server')

	def ShortTitle(self):
		return self.DefaultConfigValue('shorttitle', 'PyCS')

	def GetDate(self):
		(y, m, d, hh, mm, ss, wday, jday, dst) = time.localtime()
		
		return '%04d-%02d-%02d' % (y, m, d)

	def GetDbTime(self):
		return mx.DateTime.now()

	def GetTime(self):
		(y, m, d, hh, mm, ss, wday, jday, dst) = time.localtime()
		
		# Time of day
		pm = 'AM'
		if hh > 11: pm = 'PM'
		if hh == 0: hh = 12
		elif hh > 12: hh -= 12
		
		return '%04d-%02d-%02d %02d:%02d:%02d %s' % (y, m, d, hh, mm, ss, pm)

	def AddReferrer(self, usernum, group, referrer):
		usernum = int(usernum)
		theTime = self.GetTime()

		# add some regexps to ignore when adding Referrers
		# this should actually be pulled out of the config, I think
		userfolder = self.UserFolder(usernum)
		ignoreReferrers = [
			re.compile('^' + userfolder),
			re.compile(r'^http://127\.0\.0\.1:\d+/'),
			re.compile(r'^http://localhost:\d+/'),
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
			row = self.pdb.fetchone("SELECT id, hit_count FROM pycs_referrers WHERE usernum=%d AND usergroup=%s AND referrer=%s", (usernum, group, referrer))
			if row:
				# it is, so update the timestamp and count
				rid, count, = row
				self.pdb.execute("UPDATE pycs_referrers SET hit_count=%d, hit_time=NOW() WHERE id=%d", (count+1, rid))
			else:
				# it isn't, so add a new row to the DB
				self.pdb.execute("INSERT INTO pycs_referrers (id, usernum, usergroup, referrer, hit_time, hit_count) VALUES (NEXTVAL('pycs_referrers_id_seq'), %d, %s, %s, NOW(), 1)", (usernum, group, referrer))
			self.pdb.execute("COMMIT")
	
	def Commit(self):
		self.db.commit()
		
	def DumpData(self):
		self.DumpUsers()
	
	def DumpUsers(self):
		print "Dumping user data"
		st = self.users.structure()
		for u in self.users:
			print "USER"
			for col in st:
				print "  %s: %s" % (col.name, getattr(u, col.name))

	def FormatUsernum(self, usernum):
		
		"Converts a usernum into DB-format, e.g. 123 -> '0000123'"

		if type(usernum) != type(0):
#			print "converting %s to integer" % `usernum`
			usernum = int(usernum)
		return "%07d" % usernum

	def PatchEncodingHeader(self, str):
		"Patches the default encoding into a <?xml ...?> header"
		if self.conf.has_key('defaultencoding'):
			new = '<?xml version="1.0" encoding="%s"?>' % self.conf['defaultencoding']
			return str.replace('<?xml version="1.0"?>', new, 1)
		else:
			return str

	def save_user_to_db(self, user):
#		print "save this user to the db"
		d = user.__dict__['data']
#		print d
#		print "FIXME"
		fields = []
		values = []
		for change in user.__dict__['changed_columns']:
#			print "changed col:",change,d[change]
			fields.append(change+'=%s')
			values.append(d[change])
		sql = 'UPDATE pycs_users SET ' + ", ".join(fields) + " WHERE usernum=%d"
		values.append(d['usernum'])
		self.pdb.execute(sql, values)
#		print sql,values
		self.pdb.execute("COMMIT")
	
	def User(self, usernum):
	
		"See if the user exists, and return its DB row if it does"

		no = self.FormatUsernum(usernum)

		sql = "SELECT "+",".join(User.valid_columns)+" FROM pycs_users WHERE usernum=%d"
#		print "sql:",sql
		row = self.pdb.fetchone(sql, (int(usernum),))
#		print "row:",row
		if not row:
			print "User not found (%s)!" % (no,)
			raise NoSuchUser
			
		row = dict(zip([x.lower() for x in User.valid_columns], row))
#		print "user row from db:",row
			
		return User(self, row)

	def FindUser(self, usernum, password):
	
		"Find a user and verify the password"
		
		u = self.User(usernum)
		
		if u.password != password:
			print "Password incorrect (for %s) !" % (usernum,)
			raise PasswordIncorrect
		return u

	def FindUserByEmail(self, email, password):
		# Look for user with that address
		r = self.pdb.fetchone("SELECT usernum FROM pycs_users WHERE email=%s", (email,))
		if not r:
			raise NoSuchUser

		return self.FindUser(r[0], password)

	def NewUser(self, email, password, name):
		# Make sure we're not full already
		if self.conf.has_key('maxusernum'):
			max_users = int(self.conf['maxusernum'])
			current_num = int(self.pdb.fetchone("SELECT last_value FROM pycs_users_id_seq")[0])
			if current_num >= max_users:
				raise "Sorry; we're full!  We can't take any more users (%d so far; max %d)." % (current_num, max_users)

		usernum, = self.pdb.fetchone("SELECT NEXTVAL('pycs_users_id_seq')")
		self.pdb.execute("INSERT INTO pycs_users (usernum, email, password, name) VALUES (%d, %s, %s, %s)",
				 (usernum, pycs_db.toutf8(email), pycs_db.toutf8(password), pycs_db.toutf8(name)))
		self.pdb.execute("COMMIT")
		print "new user (%d) saved in database" % usernum
		
		# return the user row as a User object
		return self.User(usernum)
	

	def reloadAliases(self, rewriteHandler=None):
		# set the rewriteHandler for later access (if none is given,
		# use the one from the last call - the first call in pycs.py
		# sets it)
		if rewriteHandler:
			self.rewriteHandler = rewriteHandler
		else:
			rewriteHandler = self.rewriteHandler

		# add manila style aliases for users with defined "alias"
		# property and flManila true. Add normal aliases for users
		# with flManila false. To make manila style urls work, you
		# must have the corresponding rewrite rule in rewrite.conf.
		# You don't need the alias rewrite rules, those are created
		# automatically, as are the aliases settings!
		rewriteMap = []
		for usernum,alias,flManila in self.pdb.execute("SELECT usernum,alias,flManila FROM pycs_users"):
#		for row in self.users:
			if alias:
				usernum = self.FormatUsernum(usernum)
				if flManila:
					self.aliases[usernum] = "http://%s.%s" % (alias, self.ServerHostname())
				else:
					self.aliases[usernum] = "http://%s/%s" % (self.ServerHostname(), alias)
				rewriteMap.append([
					'automatic user ' + usernum + ' -> ' + self.aliases[usernum] + ' redirect',
					re.compile(r'^http://[^/]+/users/' + usernum + '(.*)$'),
					self.aliases[usernum] + r'\1',
					'R=301',
				])
				rewriteMap.append([
					'automatic /' + alias + ' rewrite to /users/' + usernum,
					re.compile(r'http://[^/]+/' + alias + r'(.*)$'),
					r'http://' + self.ServerHostname() + r'/users/' + usernum + r'\1',
					'',
				])
		rewriteHandler.resetRewriteMap(rewriteMap)

	def Alias(self, usernum, alias, flManila=0):
		formattedUsernum = self.FormatUsernum(usernum)
		if alias == '':
			if self.aliases.has_key(formattedUsernum):
				del self.aliases[formattedUsernum]
		u = self.User(usernum)
		u.alias = alias
		u.flManila = flManila
		u.save()

	def Password(self, usernum, password):
		formattedUsernum = self.FormatUsernum(usernum)
		u = self.User(usernum)
		u.password = md5.md5(password).hexdigest()
		u.save()

	def PasswordMD5(self, usernum, password_hash):
		formattedUsernum = self.FormatUsernum(usernum)
		u = self.User(usernum)
		u.password = password_hash
		u.save()

	def RecalculateUserSpace(self):
		"re-calculate space used for all users and store in the database"
		for user in self.users:
			user.bytesused = self.UserSpaceUsed(user.usernum)
			print "user %s: %d bytes used" % (user.usernum, user.bytesused)
			user.save()

	def UserSpaceUsed( self, email ):
		return usedBytes( self.UserLocalFolder( email ) )
	
	def getUserOptions( self, usernum ):
		u = self.User(usernum)
		liste = []
		liste.append(('stylesheet', u.stylesheet))
		return liste
	
	def getUserOption( self, usernum, option ):
		u = self.User(usernum)
		if option == 'stylesheet':
			return u.stylesheet
		else:
			raise KeyError(option)
	
	def getUserStylesheet(self, usernum):
		css = self.getUserOption(usernum, 'stylesheet')
		if css:
			base = self.UserFolder(usernum)
			if base[-1] == '/' and css[0] == '/':
				stylesheet = base[:-1] + css
			else:
				stylesheet = base + css
		return css

	def setUserOption( self, usernum, option, value ):
		u = self.User(usernum)
		if option == 'stylesheet':
			u.stylesheet = value
		elif option == 'disable_comments':
			u.commentsdisabled = int(value) and 1 or 0
		else:
			raise KeyError(option)
		u.save()
			
	def SpaceString(self, bytes):
		if bytes < 1024:
			return "%d bytes" % bytes
		if bytes < 1024**2:
			return "%.2f kB" % (float(bytes) / 1024.0)
		if bytes < 1024**3:
			return "%.2f MB" % (float(bytes) / 1024.0**2)
		return "%.2f GB" % (float(bytes) / 1024.0**3)

	def UsernumMunge( self, name ):
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
		return self.Munge( name )



	def Munge( self, name ):
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

	def UserLocalFolder( self, email ):
		safeEmail = self.UsernumMunge( email )
		return pycs_paths.WEBDIR + "/users/%s/" % (safeEmail,)


	def UserFolder(self, usernum):
		formattedUsernum = self.FormatUsernum(usernum)
		#print "find user folder: usernum =", usernum, " formatted usernum =",formattedUsernum
		if self.aliases.has_key(formattedUsernum):
			#print "got alias for this:", self.aliases[formattedUsernum]
			return self.aliases[formattedUsernum] + '/'
		else:
			#print "no alias"
			return self.ServerUrl() + "/users/%s/" % (formattedUsernum,)
		
	# Template renderer. An optional user number will select a stylesheet
	# if the user has set one.
	def Render(self, data, hidden=0, usernum=None):
		# Renders 'data' into html
		# data = {
		#	'title': page title,
		#	'body': body text,
		#	}

		stylesheet = '%s/pycs.css' % self.ServerUrl()
		if usernum:
			x = self.getUserStylesheet(usernum)
			if x: stylesheet = self.UserFolder(usernum) + x
		
		metatags = ''
		if hidden:
			metatags += '<meta name="robots" content="noindex,nofollow,noarchive">'
		out = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=%s">
		<title>%s: %s</title>
		<link rel="stylesheet" href="%s" type="text/css" />
		%s
	</head>
	<body>
	<h1><a class="quietLink" href="%s">%s</a>: <strong>%s</strong></h1>
		<div class="margins">
		%s
		</div>
	</body>
</html>""" % (self.DocumentEncoding(), self.LongTitle(), data['title'], stylesheet,
			metatags,
			self.ServerUrl(), self.ShortTitle(), data['title'], data['body'])
	
		return out

	def SetRewriteHandler(self, rw_h):
		self.rewrite_h = rw_h

	def SetAccessRestrictionsHandler(self, ar_h):
		self.ar_h = ar_h

	def AddUpdatePing(self, title, url):
		self.pdb.execute("DELETE FROM pycs_updates WHERE title=%s AND url=%s",
				 (pycs_db.toutf8(title), pycs_db.toutf8(url)))
		self.pdb.execute("INSERT INTO pycs_updates (update_time, title, url) VALUES (CURRENT_TIMESTAMP, %s, %s)",
				 (pycs_db.toutf8(title), pycs_db.toutf8(url)))
		self.pdb.execute("COMMIT")
