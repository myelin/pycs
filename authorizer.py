# PyCS password authorization
# ===========================

# A typical community server has a dir structure like this:

#	/ - root directory; put a suitably vague index.html here rather than restricting this.
#	|
#	+--- system - various scripts; some odd restrictions are required here
#	|	|
#	|	+--- comments.py [?(...)u=(usernum)(...)]
#	|	+--- mailto.py [?(...)usernum=(usernum)(...)]
#	|	+--- count.py
#	|	|	Restricted alongside the /users/(usernum) dir
#	|	|
#	|	+--- weblogUpdates.py
#	|	|	Public
#	|	|
#	|	+--- users.py
#	|		Sysadmins only
#	|
#	+--- users
#		|
#		+--- 0000001
#		|
#		+--- 0000002
#		|
#		+--- 0000003

# Note that, the way things are implemented, the URL the server sees
# when serving files out of a directory with a vanity name
# (e.g. /devlog instead of /users/0105568) is the /users/(usernum)
# directory, so you can take advantage of that when making auth rules.

# The user info is stored in a file called 'users.conf' (in /etc/pycs/users.conf on Linux).

# This contains a number of lines, in the format:

#	username:hashed password:visible pages

# 'username' is the username.

# 'hashed password' is the password as returned by md5.md5( password ).hexdigest()

# 'visible pages' is a comma-separated list of usernums that are to be
# visible.  You can also use the following:

# * 'public' to mean the front page (everything in the web root) and
# the /system/weblogUpdates.py (weblog updates) page.

# * 'unknown' to mean any file on the server that doesn't fit neatly
# into the diagram above

# * 'sys' to mean the sysadmin stuff in /system (not
# /system/comments.py and /system/mailto.py; those are is covered by
# the usernum visibility rules)

# * 'user' to mean *all* user blogs

# Typically a sysadmin should have 'all', a normal user should have
# 'public,123,456' (where the user is permitted to see usernums
# 0000123 and 0000456) and a 'can see everything' user should have
# 'public,user'.

# For example:

#	phil:e2fc714c4727ee9395f324cd2e7f331f:sys,1,2

# That creates a user 'phil', with password 'abcd', who can see the system files
# and blogs /users/0000001 and /users/0000002 (or whatever aliases point to them).

import re, urlparse, md5, pycs_paths, os.path

# Figure out what type of file we are looking at

UNKNOWN_FILE = 0
SYSTEM_FILE = 1
USER_FILE = 2
PUBLIC_FILE = 3

def classify_file( path, query ):
	if not query: query = ''
	print "classify",path,query
	filetype = UNKNOWN_FILE
	usernum = ''
	
	if path.startswith( '/users/' ):
		m_usernum = re.match( '^/users/0*(\d+)', path )
		if m_usernum:
			usernum = m_usernum.group( 1 )
			filetype = USER_FILE
	elif path.startswith( '/system' ):
		print "system file"
		filetype = SYSTEM_FILE
		if path.startswith( '/system/weblogUpdates.py' ):
			print "blog updates"
			filetype = PUBLIC_FILE
		elif path.startswith( '/system/comments.py' ):
			print "comments",query
			m_usernum = re.findall( 'u=0*(\d+)', query )
			if m_usernum:
				if len( m_usernum ) > 1:
					# security error: more than one usernum passed
					print "too many usernums:",m_usernum
					fail
				# we are viewing a file associated with a usernum
				usernum = m_usernum[0]
				filetype = USER_FILE
			print "blog comments:usernum",usernum
		elif path.startswith( '/system/mailto.py' ) or path.startswith( '/system/count.py' ):
			m_usernum = re.findall( 'usernum=0*(\d+)', query )
			if m_usernum:
				if len( m_usernum ) > 1:
					# security error: more than one usernum passed
					fail
				# we are viewing a file associated with a usernum
				usernum = m_usernum[0]
				filetype = USER_FILE
	else:
		folder = re.match( r'(.*)\/', path ).group( 1 )
		print "folder:",folder
		if folder == '':
			filetype = PUBLIC_FILE
	
	return filetype, usernum

def parse_users_conf( confFn ):
	# parse users.conf and work out all the users
	users = {}
	for line in open( confFn, 'rt' ).readlines():
		if line.startswith( '#' ): continue
		if line.rstrip() == '': continue
		groups = re.split( ':', line.rstrip() )
		print groups
		username, password, visibilities = groups
		if not password:
			password = md5.md5( '' ).hexdigest()
		can_see = {}
		for visibility in re.split( ',', visibilities ):
			if not visibility: continue
			if visibility == 'all':
				can_see[UNKNOWN_FILE] = 1
				can_see[SYSTEM_FILE] = 1
				can_see[PUBLIC_FILE] = 1
				can_see[USER_FILE] = 1
			elif visibility == 'public':
				can_see[PUBLIC_FILE] = 1
			elif visibility == 'etc':
				can_see[UNKNOWN_FILE] = 1
			elif visibility == 'sys':
				can_see[SYSTEM_FILE] = 1
			elif visibility == 'user':
				can_see[USER_FILE] = 1
			else:
				usernum = '%d' % ( int( visibility ), )
				visible_users = can_see.setdefault( USER_FILE, {} )
				if type( visible_users ) == type( {} ):
					visible_users[ usernum ] = 1
		users[ username ] = { 'password': password, 'can_see': can_see }
	print "users:",users
	return users

def check_permission( filetype, usernum, currentUser ):
	
	"""Checks permissions for a given file type and usernum against the 
	current user (also given) and returns 1 if the user should be able to 
	view the page, otherwise 0"""
	
	print "checking permissions for filetype",filetype,"usernum",usernum,"for user",currentUser
	
	# Everyone can see public files
	if filetype == PUBLIC_FILE: return 1
	
	# See what the current user can see
	can_see = currentUser['can_see']
	if not can_see.has_key( filetype ):
		# the current user isn't permitted to see *any* files of this type
		return 0
	
	auth_list = can_see[filetype]
	if auth_list == 1:
		# the current user is permitted to see *all* files of this type
		return 1
	if filetype == USER_FILE and auth_list.has_key( usernum ):
		# the current user is permitted to see files from this *usernum*
		return 1
	
	# couldn't find a match; give up ...
	return 0

class authorizer:
	def __init__( self ):
		self.users = parse_users_conf( os.path.join( pycs_paths.CONFDIR, 'users.conf' ) )
		
	def authorize( self, path, query, auth_info ):
		if not auth_info:
			# no login & password supplied
			auth_info = ( '', '' )

		# get username and password out of 'Authorization' HTTP header
		username, password = auth_info

		# something to keep the console happy
		print "username",username,"attempting to access",path

		# fail auth if user doesn't exist
		if not self.users.has_key( username ):
			print "user doesn't exist"
			return 0

		# user exists; grab data
		user = self.users[username]

		# fail auth if password is wrong
		if md5.md5( password ).hexdigest() != user['password']:
			print "password incorrect"
			return 0

		# password ok; see if this user has access to the requested url
		filetype, usernum = classify_file( path, query )
		return check_permission( filetype, usernum, user )
