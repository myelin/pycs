
# -*- Mode: Python -*-

#	   Author: Sam Rushing <rushing@nightmare.com>
#	Modified by: Phillip Pearson <pp@myelin.co.nz>
#	Modified by: Georg Bauer <gb@murphy.bofh.ms>
#	   Copyright 1996-2000 by Sam Rushing
#	   Copyright 2002 by Phillip Pearson and Sam Rushing
#												All Rights Reserved.
#

RCS_ID =  '$Id: pycs_webauth_handler.py,v 1.1 2003/05/15 13:10:29 gbhugo Exp $'

# support for 'basic' authenticaion.

import base64
import md5
import re
import string
import time
import counter

import default_handler

get_header = default_handler.get_header

import http_server
import producers

# This started out as the Medusa authorization handler.  Now it's specialised to work with
# Python Community Server.  If you want just a normal auth handler, import medusa.auth_handler
# instead.

# This is a 'handler' that wraps an authorization method
# around access to the resources normally served up by
# another handler.

# does anyone support digest authentication? (rfc2069)

class pycs_webauth_handler:
	def __init__ (self, set, handler, rpc_ar_h, realm='default'):
		self.set = set
		self.handler = handler
		self.realm = realm
		self.ar = rpc_ar_h
		self.pass_count = counter.counter()
		self.fail_count = counter.counter()

	def match (self, request):
		# by default, use the given handler's matcher
		return self.handler.match (request)
	
	def get_matching_header (self, head_reg, headers):
		for line in headers:
			m = head_reg.match (line)
			if m and m.end() == len(line):
				return m.groups()

	def handle_request (self, request):
		# authorize a request before handling it...
		m = self.get_matching_header (AUTHORIZATION, request.header)
		if m:
			scheme, challenge = m
			scheme = string.lower (scheme)
			if scheme == 'basic':
				cookie = challenge
				try:
					decoded = base64.decodestring (cookie)
				except:
					print 'malformed authorization info <%s>' % cookie
					request.error (400)
					return
				auth_info = string.split (decoded, ':')
			else:
				print 'unknown/unsupported auth method: %s' % scheme
				self.handle_unauthorized(request)
		else:
			auth_info = ('','')
		
		[path, params, query, fragment] = request.split_uri()
		upm = re.match(USERPATH, path)
		if upm:
			if self.ar.checkUrlAccess(upm.group(1), upm.group(2), auth_info[0], auth_info[1]):
				self.pass_count.increment()
				request.auth_info = auth_info
				self.handler.handle_request (request)
			else:
				self.handle_unauthorized(request)
		else:
			self.handler.handle_request (request)

	def handle_unauthorized (self, request):
		# We are now going to receive data that we want to ignore.
		# to ignore the file data we're not interested in.
		self.fail_count.increment()
		request.channel.set_terminator (None)
		request['Connection'] = 'close'
		request['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
		request.error (401)

	def status (self):
		# Thanks to mwm@contessa.phone.net (Mike Meyer)
		r = [
				producers.simple_producer (
						'<li>Authorization Extension : '
						'<b>Unauthorized requests:</b> %s<ul>' % self.fail_count
						)
				]
		if hasattr (self.handler, 'status'):
			r.append (self.handler.status())
		r.append (
				producers.simple_producer ('</ul>')
				)
		return producers.composite_producer (
				http_server.fifo (r)
				)

USERPATH = re.compile ( '/users/(\d+)(/.*)$' )

AUTHORIZATION = re.compile (
		#			   scheme  challenge
		'Authorization: ([^ ]+) (.*)',
		re.IGNORECASE
		)
