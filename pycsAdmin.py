#!/usr/bin/python

# Python Community Server
#
#     pycsAdmin.py: XML-RPC handler for pycsAdmin.*
#
# Copyright (c) 2002, Georg Bauer <gb@murphy.bofh.ms>
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


"""pycsAdmin XML-RPC Handler

This file handles XML-RPC requests for the pycsAdmin namespace.

Kind of like http://www.weblogs.com/RPC2 and RCS

"""

import os
import time
import sys
import re
import random
import string
import xmlrpclib

import pycs_settings
import pycs_paths
import pycs_tokens

def retmsg( failed, msg ):
	return {'flError': xmlrpclib.Boolean(failed),
		'message': msg,
		}


def createUniqueToken( password, challenge=None ):
	token = pycs_tokens.createToken( password, challenge )
	fname = os.path.join( pycs_paths.RUNDIR, token[0] )
	while os.path.exists( fname ):
		token = pycs_tokens.createToken( password, challenge )
		fname = os.path.join( pycs_paths.RUNDIR, token[0] )
	file = open( fname,'w' )
	file.write( '%s\n' % token[0] )
	file.close()
	return token


def checkUniqueToken( token, password ):
	token = pycs_tokens.checkToken( token, password )
	if token:
		fname = os.path.join( pycs_paths.RUNDIR, token[0] )
		if os.path.exists( fname ):
			file = open( fname )
			chall = file.readline()
			file.close()
			os.unlink( fname )
			chall = string.strip( chall )
			if chall == token[0]:
				return token
	return None



def makeXmlBoolean( a ):
	if a:
		return xmlrpclib.True
	else:
		return xmlrpclib.False
		

def done_msg(msg = 'Done!'):
	return retmsg(0, msg)
def param_err(n, max = None, args = 'No arguments info available'):
	if max == None:
		return retmsg(1, 'Wrong number of parameters (expected %d: %s)!' % (n, args))
	else:
		return retmsg(1, 'Wrong number of parameters (expected %d to %d: %s)!' % (n, max, args))

class pycsAdmin_handler:
	
	"pycsAdmin XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		self.adminpassword = str( random.random() )
		stat = os.stat( os.path.join( pycs_paths.CONFDIR, "pycs.conf" ) )

		if (stat[0] & 0077) == 0 or os.name == 'nt':
			if set.conf.has_key( 'adminpassword' ):
				self.adminpassword = set.conf['adminpassword']
		self.commands = {}
		for name,desc in (
			('help', 'Show table of all commands'),
			('enable', 'Enables a user'),
			('disable', 'Disables a user'),
			('list', 'List objects (users, etc.)'),
			('shuffle', 'Shuffle hit counters'),
			('recalc', 'Recalculate cached data'),
			('options', 'List options for usernum'),
			('setopt', 'Set an option for usernum'),
			('alias', 'Set alias for usernum'),
			('password', 'Set password for usernum to supplied plaintext password'),
			('password_hash', 'Set password for usernum to supplied MD5 hash'),
			('normalize_comments', 'Normalize comment usernums'),
			('list_comment_usernums', 'List all usernums in the comment table'),
			('add_comments', 'Import some comments into the comments table'),
			('renumber_comment', 'Moves a comment thread from one postid to another'),
			('renumber_all_comments', 'Moves all comments for a usernum to another usernum'),
			('email', 'Set email address for usernum' ),
			):
			self.commands[name] = [ getattr(self, name), desc ]
		
		
	def call( self, method, params ):
		print "pycsAdmin method",method #,"params",params
		
		handlers = {
			'execute': self.execute,
			'challenge': self.challenge,
			}
		
		if len( method ) == 0:
			raise "pycsAdmin method not specified"

		base = method[0]

		if base == 'challenge':
			return handlers[base]( method[1:], params )
		else:
			if len( params ) < 1:
				raise "pycsAdmin call has to few arguments"
			if not( checkUniqueToken( params[0], self.adminpassword ) ):
				raise "authorization for pycsAdmin call failed"
			if handlers.has_key( base ):
				return handlers[base]( method[1:], params[1:] )
		
		raise "pycsAdmin method not found"

	
	def challenge( self, method, params ):
		if method != []: raise "Namespace not found"

		token = createUniqueToken( self.adminpassword )

		return token[0]

	def execute( self, method, params ):
		if method != []: raise "Namespace not found"

		if len(params) != 2: raise "Not enough parameters"

		print "command:",params[0]
		print "params:",params[1]

		if self.commands.has_key( params[0] ):
			return self.commands[params[0]][0]( params[1] )
		
		return retmsg(1, 'Command %s not found!  Use command "help" for a list of commands.' % ( params[0], ))
		

	def help( self, params ):
		res = []

		for c in self.commands.keys():
			res.append( [ c,self.commands[c][1] ] )

		res.sort( lambda a,b: cmp( a[0],b[0] ) )

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			'columns': [ 'command', 'description' ],
			'table': res,
			}

	def shuffle( self, params ):
		if len(params) != 1:
			return retmsg(1, msg='Wrong number of parameters!')

		if params[0] == 'hits':
			for row in self.set.users:
				row.hitsyesterday = row.hitstoday
				row.hitstoday = 0
			self.set.Commit()
		else:
			return retmsg(1, 'Unknown object-spec %s' % params[0])
		return done_msg()
			
	def recalc( self, params ):
		if len(params) != 1:
			return param_err(1)

		if params[0] == 'diskspace':
			self.set.RecalculateUserSpace()
		else:
			return retmsg(1, 'Unknown object-spec %s' % params[0])
		return done_msg()

	def options( self, params ):
		res = []

		if len(params) != 1:
			return param_err(1)

		user = self.set.User( params[0] )

		cols = ['option', 'value']
		for option in self.set.getUserOptions(user.usernum):
			res.append(list(option))

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			'columns': cols,
			'table': res
			}

	def setopt( self, params ):
		res = []

		if len(params) != 3:
			return param_err(3)

		user = self.set.User( params[0] )

		self.set.setUserOption(user.usernum,params[1],params[2])

		return done_msg()

	def list( self, params ):
		cols = []
		res = []

		if len(params) != 1:
			return param_err(1)

		if params[0] == 'users':
			sth = self.set.users.ordered(1)
			cols = ['usernum', 'name', 'email']
			for row in sth:
				res.append( [row.usernum, row.name, row.email] )
		elif params[0] == 'enabled':
			sth = self.set.users.select( {'disabled': 0} )
			cols = ['usernum', 'name', 'email']
			for row in sth:
				res.append( [row.usernum, row.name, row.email] )
		elif params[0] == 'disabled':
			sth = self.set.users.select( {'disabled': 1} )
			cols = ['usernum', 'name', 'email']
			for row in sth:
				res.append( [row.usernum, row.name, row.email] )
		elif params[0] == 'rewrites':
			cols = ['title']
			for row in self.set.rewriteHandler.rewriteMap:
				res.append( [row[0]] )
		elif params[0] == 'aliases':
			cols = ['usernum', 'alias', 'flManila']
			for row in self.set.users:
				if row.alias:
					flag = 'False'
					if row.flManila:
						flag = 'True'
					res.append( [row.usernum, row.alias, flag] )
		else:
			return retmsg(1, 'Unknown object-spec %s' % params[0])

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			'columns': cols,
			'table': res,
			}

	def enable( self, params ):
		res = []

		if len(params) != 1:
			return param_err(1)

		user = self.set.User( params[0] )
		user.disabled = 0
		self.set.Commit()

		return done_msg()

	def disable( self, params ):
		res = []

		if len(params) != 1:
			return param_err(1)

		user = self.set.User( params[0] )
		user.disabled = 1
		self.set.Commit()

		return done_msg()

	def alias( self, params ):
		if (len(params) < 2) or (len(params) > 3):
			return param_err(2,3)
		if params[0] == 'del':
			if len(params) != 2:
				return {
					'flError': xmlrpclib.True,
					'message': 'Wrong number of parameters for del!',
					}
		else:
			if len(params) != 3:
				return {
					'flError': xmlrpclib.True,
					'message': 'Wrong number of parameters, alias is needed!',
					}

		try:
			user = self.set.User( params[1] )
		except:
			return {
				'flError': xmlrpclib.True,
				'message': 'User %s not found' % params[1],
				}

		if params[0] == 'simple':
			self.set.Alias( params[1], params[2], 0 )
			self.set.reloadAliases()
		elif params[0] == 'manila':
			self.set.Alias( params[1], params[2], 1 )
			self.set.reloadAliases()
		elif params[0] == 'del':
			self.set.Alias( params[1], '', 0 )
			self.set.reloadAliases()
		else:
			return {
				'flError': xmlrpclib.True,
				'message': 'Unknown alias subcommand %s' % params[0],
				}

		self.set.Commit()

		return done_msg()


	def password( self, params ):
		if len(params) != 2:
			return param_err(2, args="usernum, password")
		try:
			user = self.set.User( params[0] )
		except:
			return {
				'flError': xmlrpclib.True,
				'message': 'User %s not found' % params[1],
				}

		self.set.Password( params[0], params[1] )

		self.set.Commit()

		return done_msg()

	def password_hash(self, params):
		if len(params) != 2:
			return param_err(2, args="usernum, md5 hash")
		try:
			user = self.set.User( params[0] )
		except:
			return {
				'flError': xmlrpclib.True,
				'message': 'User %s not found' % params[1],
				}
		self.set.PasswordMD5( params[0], params[1] )
		self.set.Commit()
		return done_msg()

	def email( self, params ):
		if len(params) != 2:
			return param_err(2, args="usernum, email-address")
		try:
			user = self.set.User( params[0] )
		except:
			return {
				'flError': xmlrpclib.True,
				'message': 'User %s not found' % params[1],
				}
		user.email = params[1]
		self.set.Commit()
		return done_msg()

	def normalize_comments( self, params ):
		if len(params) != 0:
			return param_err(0)
		# now run through all comments and normalize the usernums
		ct = self.set.getCommentTable()
		count = changed = 0
		changes = []
		for row in ct:
			count += 1
			old_user = row.user
			new_user = str(int(old_user))
			if old_user != new_user:
				changed += 1
				changes.append('%s -> %s' % (old_user, new_user))
				row.user = new_user
				assert row.user == new_user
		self.set.Commit()
		# succeeded, we assume!
		return done_msg("Normalized %d usernums out of %d in the comment table, changes: %s" % (changed, count, ", ".join(changes)))

	def list_comment_usernums( self, params ):
		if len(params): return param_err(0)
		
		ct = self.set.getCommentTable()
		usernums = {}
		for row in ct:
			usernums.setdefault(row.user, []).append(row.paragraph)
		keys = [(int(x), x) for x in usernums.keys()]
		keys.sort()
		ret = "Usernums:\n"
		for n,k in keys:
			ret += "%s: %s\n" % (k, ", ".join(usernums[k]))
		return done_msg(ret)
	
	def _make_comment_block(self, u, p):
		"retrieve row in comments table for a post, creating it if it doesn't exist"
		ct = self.set.getCommentTable()
		rows = ct.select({'user': u, 'paragraph': p})
		if not len(rows):
			ct.append(user=u, paragraph=p)
			rows = ct.select({'user': u, 'paragraph': p})
		cmt_block = rows[0]
		return cmt_block

	def add_comments( self, params ):
		if len(params) != 2: return param_err(2)

		import comments

		ret = ''
		u, plist = params
		for p,cmts in plist.items():
			# prepare db space for this post
			cmt_block = _make_comment_block(u, p)

			# add all comments for this post
			for cmt in cmts:
				ret += 'u %s p %s cmt %s\n' % (u, p, `cmt`)
				when = [x for x in cmt['when']]
				while len(when) < 9: when += [0]
				ci = {'name': cmt['from'].encode('utf-8'),
				      'email': cmt.has_key('email') and cmt['email'].encode('utf-8') or '',
				      'url': cmt['url'].encode('utf-8'),
				      'date': time.strftime(comments.STANDARDDATEFORMAT, when),
				      'comment': cmt['comment'].strip().encode('utf-8'),
				      }
				print ci
				rows = cmt_block.notes.select(ci)
				print rows
				if len(rows):
					ret += "already got comment %s\n" % `ci`
				else:
					ret += "added comment %s\n" % `ci`
					cmt_block.notes.append(ci)

		self.set.Commit()
		
		return done_msg(ret)

	def _move_comments(self, cmt_block, newusernum, newpostid):
		ret = ''
		# now copy the comments over to the post on the new userid
		ret += "getting handle to comment block for %s/%s\n" % (newusernum, newpostid)
		new_block = self._make_comment_block(newusernum, newpostid)
		ret += "[block: u=%s p=%s]\n" % (new_block.user, new_block.paragraph)

		for cmt in cmt_block.notes:
			cmt_v = {'date': cmt.date, 'name': cmt.name, 'email': cmt.email, 'url': cmt.url, 'comment': cmt.comment}
			if len(new_block.notes.select(cmt_v)):
				ret += "comment with date %s is already in there\n" % cmt.date
			else:
				ret += "copying comment with date %s\n" % cmt.date
				new_block.notes.append(cmt)
		ret += "deleting comments from original thread\n"
		cmt_block.notes[:] = []
			
		return ret

	def renumber_comment( self, params ):
		if len(params) != 4: return param_err(4)

		usernum, oldid, newusernum, newid = params

		# setup
		import comments
		ret = ''
		ct = self.set.getCommentTable()

		# get the comments for the specified post
		blk_v = {'user': usernum, 'paragraph': oldid}
		rows = ct.select(blk_v)
		if len(rows):
			cmt_block = rows[0]
		else:
			return retmsg(1, "Comment %s does not exist for usernum %s" % (oldid, usernum))

		ret += "found comment block %s\n" % `blk_v`
		ret += self._move_comments(cmt_block, newusernum, newid)

		# make it permanent
		ret += "committing to db\n"
		self.set.Commit()

		return done_msg("Comment %s for usernum %s renumbered to %s for usernum %s\n\ndetails:\n%s" % (oldid, usernum, newid, newusernum, ret))

	def renumber_all_comments(self, params):
		if len(params) != 2: return param_err(2)

		usernum, newusernum = params
		ret = ''
		ct = self.set.getCommentTable()
		for row in ct.select({"user": usernum}):
			ret += "moving comments for u=%s p=%s to u=%s p=%s...\n" % (row.user, row.paragraph, newusernum, row.paragraph)
			ret += self._move_comments(row, newusernum, row.paragraph)
			ret += "\n"

		return done_msg("Moved comments for usernum %s to usernum %s\n\ndetails:\n%s" % (usernum, newusernum, ret))

if __name__=='__main__':
	# Testing
	s = xmlrpclib.Server( 'http://www.pycs.net/RPC2' )
	print s.pycsAdmin.execute( 'help' )
	
