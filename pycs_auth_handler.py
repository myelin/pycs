# -*- Mode: Python -*-

#	   Author: Sam Rushing <rushing@nightmare.com>
#	Modified by: Phillip Pearson <pp@myelin.co.nz>
#	   Copyright 1996-2000 by Sam Rushing
#	   Copyright 2002 by Phillip Pearson and Sam Rushing
#												All Rights Reserved.
#

RCS_ID =  '$Id: pycs_auth_handler.py,v 1.2 2002/10/27 11:22:48 myelin Exp $'

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

class pycs_auth_handler:
	def __init__ (self, set, handler, realm='default'):
		import authorizer
		self.authorizer = authorizer.authorizer()
		self.set = set
		self.handler = handler
		self.realm = realm
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
			#elif scheme == 'digest':
			#	   print 'digest: ',AUTHORIZATION.group(2)
			else:
				print 'unknown/unsupported auth method: %s' % scheme
				self.handle_unauthorized(request)
		else:
			# list both?  prefer one or the other?
			# you could also use a 'nonce' here. [see below]
			#auth = 'Basic realm="%s" Digest realm="%s"' % (self.realm, self.realm)
			#nonce = self.make_nonce (request)
			#auth = 'Digest realm="%s" nonce="%s"' % (self.realm, nonce)
			#request['WWW-Authenticate'] = auth
			#print 'sending header: %s' % request['WWW-Authenticate']
			auth_info = None
			#self.handle_unauthorized (request)
		[path, params, query, fragment] = request.split_uri()
		if self.authorizer.authorize (path, query, auth_info):
			self.pass_count.increment()
			request.auth_info = auth_info
			self.handler.handle_request (request)
		else:
			self.handle_unauthorized (request)

	def handle_unauthorized (self, request):
		# We are now going to receive data that we want to ignore.
		# to ignore the file data we're not interested in.
		self.fail_count.increment()
		request.channel.set_terminator (None)
		request['Connection'] = 'close'
		request['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
		request.error (401)

	def make_nonce (self, request):
		"A digest-authentication <nonce>, constructed as suggested in RFC 2069"
		ip = request.channel.server.ip
		now = str(long(time.time()))
		if now[-1:] == 'L':
			now = now[:-1]
		private_key = str (id (self))
		nonce = string.join ([ip, now, private_key], ':')
		return self.apply_hash (nonce)

	def apply_hash (self, s):
		"Apply MD5 to a string <s>, then wrap it in base64 encoding."
		m = md5.new()
		m.update (s)
		d = m.digest()
		# base64.encodestring tacks on an extra linefeed.
		return base64.encodestring (d)[:-1]

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

class dictionary_authorizer:
	def __init__ (self, dict):
		self.dict = dict

	def authorize (self, auth_info):
		[username, password] = auth_info
		if (self.dict.has_key (username)) and (self.dict[username] == password):
			return 1
		else:
			return 0

AUTHORIZATION = re.compile (
		#			   scheme  challenge
		'Authorization: ([^ ]+) (.*)',
		re.IGNORECASE
		)
