# Python Community Server
#
#     search.py: search your weblog using ht://Dig (EXPERIMENTAL)
#
# Copyright (c) 2003, Phillip Pearson <pp@myelin.co.nz>
# 
# This file is released under the MIT license, but it depends on ht://Dig,
# which is under the following license:
#
# 	Part of the ht://Dig package   <http://www.htdig.org/>
# 	Copyright (c) 1995-2000 The ht://Dig Group
# 	For copyright details, see the file COPYING in your distribution
# 	or the GNU Public License version 2 or later
# 	<http://www.gnu.org/copyleft/gpl.html>
#
# 	$Id: htdig.py,v 1.2 2003/10/15 11:27:52 myelin Exp $
#
# So I guess if you use search.py, your copy of PyCS falls under the GPL.
# Don't install htsearch to keep it under the MIT license.  Your call :-)
#

import md5
import string
import pycs_settings
import re
import cgi
import smtplib
import socket
import os
import sys
import binascii
import base64

# See pycs_module_handler.py for info on how modules work

# We should be able to get at the following globals:

#	request: an http request object
#		try request.split_uri() to get some info about the request


[path, params, query, fragment] = request.split_uri()
query = util.SplitQuery( query )
form = util.SplitQuery( input_data.read() )

request['Content-Type'] = 'text/html; charset=%s' % set.DocumentEncoding()

page = {
	'title': _('Search results'),
	'body': """<p>Something went wrong; there should be some text here!</p>
		<p>Mail <a href="mailto:pp@myelin.co.nz">Phil</a> at 
		<a href="http://www.myelin.co.nz/">Myelin</a> if you
		think something is broken.</p>""",
	}

# Actually generate the output

s = ""

def esc(s):
	return cgi.escape(s, 1)

AUTHORIZATION = re.compile (
		#			   scheme  challenge
		'Authorization: ([^ ]+) (.*)',
		re.IGNORECASE
		)

def get_matching_header(head_reg, headers):
	for line in headers:
		m = head_reg.match (line)
		if m and m.end() == len(line):
			return m.groups()

def auth_info():
	# find auth info
	m = get_matching_header(AUTHORIZATION, request.header)
	if m:
		scheme, challenge = m
		scheme = string.lower (scheme)
		if scheme == 'basic':
			cookie = challenge
			try:
				decoded = base64.decodestring (cookie)
			except binascii.error:
				print 'malformed authorization info <%s>' % cookie
				return None
			return string.split (decoded, ':')
		else:
			print 'unknown/unsupported auth method: %s' % scheme
			return None
	else:
		return None

ai = auth_info()
# <path>;<params>?<query>#<fragment>
path_regex = re.compile(
    #      path      params    query   fragment
        r'([^;?#]*)(;[^?#]*)?(\?[^#]*)?(#.*)?'
		)

def split_uri(uri):
	m = path_regex.match(uri)
	if not m or (m.end() != len(uri)):
		raise ValueError, "Broken URI"
	else:
		return m.groups()

def split_url(url):
	if url.startswith('http://'):
		firstslash = url.find('/', 7)
		if firstslash == -1:
			return split_uri('/')
		else:
			return split_uri(url[firstslash:])

def authorize(url):
	# rewrite url so we get something the authorizer can handle
	#print "auth for url:",url
	url = set.rewrite_h.rewriteUrl(url, quiet=1)
	#print "rewritten to:",url
	# split it up and authorize
	try:
		[path, params, query, fragment] = split_url(url)
	except ValueError:
		return 0
	return set.authorizer.authorize(path, query, ai, quiet=1)

URLUSER = re.compile(r'/users/(\d+)(/.*)$')

def webauthorize(url):
	url = set.rewrite_h.rewriteUrl(url, quiet=1)
	upm = URLUSER.match(url)
	auth_info = (,)
	if ai:
		auth_info = ai
	if upm:
		if set.ar_h.checkUrlAccess(upm.group(1), upm.group(2), auth_info[0], auth_info[1]) == 0:
			return 0
	return 1
	
def exclude_url_callback(url):
	"url exclusion callback; checks a url and returns 1 if it should show in the search results"
	if webauthorize(url) == 0:
		return 0
	if set.authorizer is not None:
		# we've got an authorizer; refuse access to the file if the current
		# auth settings won't let the user see it.
		#print "we've got an authorizer"
		try:
			if not authorize(url):
				#print "it didn't like it!"
				return 0
		except:
			print "exception trying to run authorizer:"
			import traceback
			traceback.print_exc()
	# authentication turned off or the current user has permission to see the
	# url.  now check to see if it's a silly url that we don't want to show anyway
	# (rss.xml, mailto pages, etc).
	if (#not url.startswith('http://www.pycs.net')
	    url.endswith('.xml') or url.endswith('.opml')
	    or (url.find('/system/mailto.py?') != -1)
	    or url.endswith('/system/login.py')
	    or url.endswith('&format=rss')):
		return 0
	return 1

def pycs_htsearch(qs, cb, conf):
	"""fork and search; cgi-style

	qs = query string to pass to htsearch

	cb = url exclusion callback (takes a string, returns true to
	say a url should show in the search results or false to say
	that it should not)

	conf = full path to htdig.conf file (usually
	$htdig_prefix/conf/htdig.conf).

	"""
	htspath = set.conf['htsearchpath']
	r, w = os.pipe()

	pid = os.fork()
	if pid:
		# we are the parent
		print "fork()ed and created pid %d" % pid
		os.close(w)
		r = os.fdopen(r)
		txt = r.read()
		os.waitpid(pid, 0)
		print "pid %d is finished; displaying results" % pid
	else:
		# we are the child
		try:
			os.close(r)
			sys.stdout = w = os.fdopen(w, 'w')
			sys.path.insert(0, htspath)
			import _htsearch
			result = _htsearch.search(qs, cb, conf)
			w.write(result)
			w.close()
		finally:
			sys.exit(0) # medusa will catch this ... have to be able to properly die :/

	return txt

def search(words):
	import urllib
	qs = urllib.urlencode((
		('words', words),
		))
	conf = set.conf['htsearchconf']
	return pycs_htsearch(qs, exclude_url_callback, conf)

if set.conf.get('enablehtdig', 'no') != 'yes':

	s += """<p>Searching has not been enabled by your administrator.</p>
	<p>(The <code>enablehtdig</code> variable in <code>pycs.conf</code>
	needs to be set to <code>yes</code>.)</p>"""

elif not set.conf.has_key('htsearchpath'):

	s += """<p>I don't know how to get to the ht://Dig search CGI.</p>
	<p>(The administrator needs to set the <code>htsearchpath</code> variable in <code>pycs.conf</code>.)</p>"""

elif not set.conf.has_key('htsearchconf'):

        s += """<p>I don't know how to get to the ht://Dig configuration file.</p>
        <p>(The administrator needs to set the <code>htsearchconf</code> variable in <code>pycs.conf</code>.)</p>"""

else:
	search_terms = query.get('q', query.get('words', ''))

	s += """<form method="GET">
	Search: <input type="text" size="80" name="q" value="%s" />
	</form>""" % esc(search_terms)

	if search_terms:
		s += search(search_terms)

page['body'] = s
s = set.Render( page )

request['Content-Length'] = len(s)
request.push( s )
request.done()
