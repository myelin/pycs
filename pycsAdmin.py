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
import sys
import re
import random
import string
import xmlrpclib

import pycs_settings
import pycs_paths
import pycs_tokens


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
		




class pycsAdmin_handler:
	
	"pycsAdmin XML-RPC functions"
	
	def __init__( self, set ):
		self.set = set
		self.adminpassword = str( random.random() )
		stat = os.stat( os.path.join( pycs_paths.CONFDIR, "pycs.conf" ) )

		if (stat[0] & 0077) == 0:
			if set.conf.has_key( 'adminpassword' ):
				self.adminpassword = set.conf['adminpassword']
		self.commands = {
			'help': [ self.help, 'Show table of all commands' ],
			'enable': [ self.enable, 'Enables a user' ],
			'disable': [ self.disable, 'Disables a user' ],
			'list': [ self.list, 'List objects (users, etc.)' ],
			'shuffle': [ self.shuffle, 'Shuffle hit counters' ],
			'alias': [ self.alias, 'Set alias for usernum' ],
		}
		
		
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
		
		return {
			'flError': xmlrpclib.True,
			'message': 'Command %s not found!' % ( params[0], ),
			}
		

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
			return {
				'flError': xmlrpclib.True,
				'message': 'Wrong number of parameters!',
				}

		if params[0] == 'hits':
			for row in self.set.users:
				row.hitsyesterday = row.hitstoday
				row.hitstoday = 0
			self.set.Commit()
		else:
			return {
				'flError': xmlrpclib.True,
				'message': 'Unknown object-spec %s' % params[0],
				}
		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			}
			

	def list( self, params ):
		cols = []
		res = []

		if len(params) != 1:
			return {
				'flError': xmlrpclib.True,
				'message': 'Wrong number of parameters!',
				}

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
			return {
				'flError': xmlrpclib.True,
				'message': 'Unknown object-spec %s' % params[0],
				}

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			'columns': cols,
			'table': res,
			}

	def enable( self, params ):
		res = []

		if len(params) != 1:
			return {
				'flError': xmlrpclib.True,
				'message': 'Wrong number of parameters!',
				}

		user = self.set.User( params[0] )
		user.disabled = 0
		self.set.Commit()

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			}

	def disable( self, params ):
		res = []

		if len(params) != 1:
			return {
				'flError': xmlrpclib.True,
				'message': 'Wrong number of parameters!',
				}

		user = self.set.User( params[0] )
		user.disabled = 1
		self.set.Commit()

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			}

	def alias( self, params ):
		if (len(params) < 2) or (len(params) > 3):
			return {
				'flError': xmlrpclib.True,
				'message': 'Wrong number of parameters!',
				}
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

		return {
			'flError': xmlrpclib.False,
			'message': 'Done!',
			}


if __name__=='__main__':
	# Testing
	s = xmlrpclib.Server( 'http://www.pycs.net/RPC2' )
	print s.pycsAdmin.execute( 'help' )
	
